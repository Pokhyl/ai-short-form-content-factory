"""Owner-facing Studio API for a separate, guarded factory_next worker.

A user-submitted topic becomes a NEW UUID with independent free-tier
provider budgets and immutable stage checkpoints. Never revives an
ambiguous stage or reuses prior audio. Does not touch factory_v3 routes.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit
from uuid import UUID, uuid4

from factory_v3.preflight import asset_path, validate_asset
from factory_v3.runtime import Runtime, load_settings
from factory_v3.server import byte_range
from .pipeline import Pipeline
from .wiring import connected_adapters, register_next

PREFIX="/factory-next"
STAGES=("research","materials","story","voice","alignment","edit","render","audit")
DAY_LIMIT=6
MAX_ACTIVE=2
MAX_WAITING=3
WEB=Path(__file__).with_name("studio_web")/"index.html"


class TTSBillingHold(RuntimeError):
    """No job admission or provider sends without external billing verification."""


def safe_id(value):
    return str(UUID(str(value)))


class Studio:
    def __init__(self, root, settings, revision):
        self.root=Path(root)
        self.records=self.root/"factory-next-studio"/"jobs"
        self.records.mkdir(parents=True,exist_ok=True)
        self.revision=revision
        self.runtime=Runtime(settings,self.root,revision)
        self.pipeline_root=self.root/"factory-next-states"
        self.lock=threading.RLock()
        self.workers=ThreadPoolExecutor(max_workers=1,thread_name_prefix="factory-next-stage")
        self.inflight=set()
        self.stop=threading.Event()
        self.scheduler=threading.Thread(target=self._schedule,daemon=True,name="factory-next-scheduler")
        self.scheduler.start()

    def generation_enabled(self):
        # Server-owned verified evidence, never a browser-supplied override.
        # The internal PostgreSQL usage counter alone cannot establish this.
        return self.runtime.settings.get("google_tts_external_usage_verified") is True

    def require_generation_enabled(self):
        if not self.generation_enabled():
            raise TTSBillingHold("Google TTS billing unverified; generation paused")

    def public_status(self):
        return {"generation_enabled":self.generation_enabled(),
                "reason":None if self.generation_enabled() else "GOOGLE_TTS_BILLING_UNVERIFIED",
                "history_available":True}

    def record(self,job):
        return self.records/(safe_id(job)+".json")

    def entries(self):
        rows=[]
        for path in self.records.glob("*.json"):
            try:
                row=json.loads(path.read_text())
                if row["id"]!=safe_id(path.stem):
                    continue
                rows.append(row)
            except (ValueError,OSError,KeyError,TypeError):
                continue
        return sorted(rows,key=lambda x:x.get("created_at",""),reverse=True)

    def pipeline(self,job,with_adapters=False):
        return Pipeline(self.pipeline_root,
                        connected_adapters(self.runtime,job) if with_adapters else None,
                        self.revision)

    def snapshot(self,job):
        if not self.record(job).is_file():
            raise FileNotFoundError("unknown studio video")
        return self.pipeline(job).snapshot(job)

    @staticmethod
    def _admission_date(row):
        """Admission consumes the daily START limit, not the submission date.

        Historical completed records predate the queue and were admitted when
        created. Queued records have eligible_after but no admitted_at.
        """
        if row.get("registration")!="complete":
            return None
        if row.get("admitted_at"):
            return row["admitted_at"][:10]
        if "eligible_after" not in row:
            return row.get("created_at","")[:10]
        return None

    def _active_count(self,rows):
        active=0
        for row in rows:
            if row.get("registration")=="registering":
                active+=1
                continue
            if not self._admission_date(row):
                continue
            try:
                state=self.pipeline(row["id"]).snapshot(row["id"])
                if state["status"] in ("ready","running","checking",
                                       "checking_provider","deferred","provider_wait"):
                    active+=1
            except (OSError,ValueError,KeyError):
                # Uncertain registration/checkpoint must not free capacity.
                active+=1
        return active

    def _admit_waiting(self,now=None):
        """Register exactly one due request, then persist its runnable state.

        Queued items carry NO PostgreSQL preparation, so a new code version can
        safely register them under its own current immutable revision. Before
        any uncertain external registration, the exclusive record is marked
        'registering': a crash will NOT cause automatic duplicate dispatch.
        """
        if not self.generation_enabled():
            return None
        now=now or datetime.now(timezone.utc)
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("aware admission clock required")
        with self.lock:
            rows=self.entries()
            if any(x.get("registration")=="registering" for x in rows):
                # An uncertain prior registration needs explicit reconciliation.
                return None
            if sum(self._admission_date(x)==now.date().isoformat() for x in rows)>=DAY_LIMIT:
                return None
            if self._active_count(rows)>=MAX_ACTIVE:
                return None
            for row in reversed(rows):
                if row.get("registration")!="queued":
                    continue
                due=datetime.fromisoformat(row["eligible_after"])
                if due.tzinfo is None or due.utcoffset() is None or due>now:
                    continue
                row["registration"]="registering"
                self._save_record(row)
                job=row["id"];request=row["request"]
                registered=register_next(self.runtime,job,request["topic"],
                                         request["language"],request["seconds"])
                if registered.get("created") is not True:
                    raise RuntimeError("queued registration uncertain")
                self.pipeline(job).create(job,request["topic"],
                                          request["language"],request["seconds"])
                row["registration"]="complete"
                row["admitted_at"]=now.isoformat()
                row["registered_revision"]=self.revision
                self._save_record(row)
                return job
        return None

    def create(self,data):
        if not isinstance(data,dict) or set(data)!={"topic","language","seconds"}:
            raise ValueError("only topic, language and duration are accepted")
        topic,language,seconds=data["topic"],data["language"],data["seconds"]
        if (not isinstance(topic,str) or not 1<=len(topic.strip())<=300
                or language not in ("pl","en","ru","uk")
                or type(seconds) is not int or seconds not in (15,30,45,60)):
            raise ValueError("invalid topic, language or duration")
        topic=topic.strip()
        self.require_generation_enabled()
        now=datetime.now(timezone.utc)
        with self.lock:
            # Re-check under the durable admission lock.
            self.require_generation_enabled()
            rows=self.entries()
            today=now.date().isoformat()
            used=sum(self._admission_date(x)==today for x in rows)
            active=self._active_count(rows)
            waiting=sum(x.get("registration") in ("queued","registering")
                        for x in rows)
            delayed=(used>=DAY_LIMIT or active>=MAX_ACTIVE or waiting>0)
            if delayed and waiting>=MAX_WAITING:
                raise OverflowError("Studio waiting queue is full")
            job=str(uuid4())
            record={"id":job,"request":{"topic":topic,"language":language,"seconds":seconds},
                    "created_at":now.isoformat(),
                    "registration":"queued" if delayed else "pending"}
            if delayed:
                # Waiting in the queue does not authorize a provider request.
                # Daily admission allowance resets at 00:00 UTC.
                due=(datetime.combine(now.date()+timedelta(days=1),
                                      datetime.min.time(),tzinfo=timezone.utc)
                     if used>=DAY_LIMIT else now)
                record["eligible_after"]=due.isoformat()
            # Store a unique durable identifier before any external operation.
            # Delayed items intentionally do NOT register a preparation yet.
            # Its registration and code revision are established at admission.
            with self.record(job).open("x") as stream:
                json.dump(record,stream,ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            if not delayed:
                registered=register_next(self.runtime,job,topic,language,seconds)
                if registered.get("created") is not True:
                    raise RuntimeError("new job registration uncertain")
                self.pipeline(job).create(job,topic,language,seconds)
                record["registration"]="complete"
                record["admitted_at"]=now.isoformat()
                record["registered_revision"]=self.revision
                self._save_record(record)
        if not delayed:
            self.enqueue(job)
        return {"id":job,"status":"queued_for_quota" if delayed else "queued"}

    def _save_record(self,record):
        path=self.record(record["id"])
        temporary=path.with_suffix(".tmp")
        with temporary.open("w") as stream:
            json.dump(record,stream,ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary,path)

    def enqueue(self,job):
        if not self.generation_enabled():
            return
        with self.lock:
            if not self.generation_enabled():
                return
            # A queued submission is never dispatched before durable admission.
            if hasattr(self,"records"):
                row=json.loads(self.record(job).read_text())
                if row.get("registration")!="complete":
                    return
            if job in self.inflight:
                return
            self.inflight.add(job)
        try:
            self.workers.submit(self._advance,job)
        except BaseException:
            with self.lock:
                self.inflight.discard(job)
            raise

    def _advance(self,job):
        try:
            if not self.generation_enabled():
                return
            pipeline=self.pipeline(job,with_adapters=True)
            for _ in STAGES:
                s=pipeline.snapshot(job)
                if s["status"] not in ("ready","deferred","provider_wait"):
                    break
                if s["status"]=="provider_wait":
                    try:
                        due=datetime.fromisoformat(s["provider_wait_receipt"]["retry_at"]).timestamp()
                    except (KeyError,ValueError,TypeError,OverflowError):
                        break
                    if time.time()<due:
                        break
                if s["status"]=="deferred":
                    prior=s.get("preflight_deferrals",{}).get(s.get("next_stage"),{})
                    if time.time()<prior.get("next_retry_at",float("inf")):
                        break
                result=pipeline.step(job)
                if result["status"]!="ready":
                    break
        except Exception:
            # Pipeline preserves its own immutable error checkpoint. Never
            # convert a running or unknown provider operation into a retry.
            pass
        finally:
            with self.lock:
                self.inflight.discard(job)

    def _schedule(self):
        while not self.stop.wait(8):
            if not self.generation_enabled():
                continue
            try:
                admitted=self._admit_waiting()
                if admitted is not None:
                    self.enqueue(admitted)
            except Exception:
                # Preserve queued jobs for the next safe scheduler check.
                pass
            for row in self.entries():
                if row.get("registration")!="complete":
                    continue
                job=row["id"]
                try:
                    state=self.pipeline(job).snapshot(job)
                    status=state["status"]
                    if status=="ready":
                        self.enqueue(job)
                    elif status=="provider_wait":
                        due=datetime.fromisoformat(state["provider_wait_receipt"]["retry_at"])
                        if due.timestamp()<=time.time():
                            self.enqueue(job)
                    elif status=="deferred":
                        stage=state.get("next_stage")
                        gate=state.get("preflight_deferrals",{}).get(stage,{})
                        if gate.get("next_retry_at",float("inf"))<=time.time():
                            self.enqueue(job)
                except Exception:
                    continue

    def detail(self,job):
        job=safe_id(job)
        record=json.loads(self.record(job).read_text())
        if record.get("registration")!="complete":
            queued=record.get("registration")=="queued"
            hold=not self.generation_enabled()
            return {"id":job,"request":record["request"],
                    "status":"billing_hold" if hold else (
                        "queued_for_quota" if queued else "registration_pending"),
                    "generation_on_hold":hold,
                    "eligible_after":record.get("eligible_after") if queued else None,
                    "next_stage":"research","completed_stages":[],
                    "error_type":None,"failure_reason":None,"retry_at":None,
                    "script":"","scenes":[],"sources":[],"photo_count":0,
                    "voice_duration_ms":None,"machine_pass":False,"video_url":None,
                    "video_sha256":None,"source_revision":None}
        state=self.snapshot(job)
        outputs=state.get("outputs",{})
        research=outputs.get("research",{})
        assets={a["id"]:a for a in outputs.get("materials",{}).get("assets",[])}
        visuals={p["id"]:p for p in outputs.get("materials",{}).get("photos",[])}
        active_story=outputs.get("voice",{}).get("reviewed_story",outputs.get("story",{}))
        scenes=[]
        for i,scene in enumerate(active_story.get("scenes",[])):
            asset=assets.get(scene.get("material_id"),{})
            scenes.append({"id":scene.get("id"),"narration":scene.get("narration",""),
                           "photo_url":PREFIX+"/api/jobs/"+job+"/photo/"+str(i),
                           "visual_kind":visuals.get(scene.get("material_id"),{}).get("visual_kind","photograph"),
                           "source_url":asset.get("source_url",""),
                           "author":asset.get("author",""),
                           "license":asset.get("license",""),
                           "license_url":asset.get("license_url","")})
        complete=(state["status"]=="complete" and
                  outputs.get("audit",{}).get("passed") is True and
                  outputs.get("render",{}).get("sha256")==outputs.get("audit",{}).get("sha256"))
        sources=[{"title":x.get("title",""),"url":x.get("url","")}
                 for x in research.get("evidence",{}).get("sources",[])
                 if isinstance(x,dict)]
        # Owner-facing, read-only diagnosis from the durable failure receipt.
        # Never expose provider headers, messages, tokens or execution data.
        failure_reason=None
        if state["status"]=="needs_attention" and state.get("error_type")=="HTTPFailure":
            try:
                failure_reason=self.runtime.ledger._call(
                    "SELECT CASE WHEN EXISTS("
                    "SELECT 1 FROM factory_v3.preparation_calls "
                    "WHERE preparation_id=%s::uuid AND state='unknown' "
                    "AND response->>'error_reason'='OAUTH_GRANT_REJECTED'"
                    ") THEN 'GOOGLE_OAUTH_RECONNECT_REQUIRED' "
                    "WHEN EXISTS(SELECT 1 FROM factory_v3.preparation_calls "
                    "WHERE preparation_id=%s::uuid AND kind='gemini' "
                    "AND state='unknown' AND error_code='HTTPFailure' "
                    "AND response->>'status'='429' "
                    "AND response->>'error_status'='RESOURCE_EXHAUSTED') "
                    "THEN 'GEMINI_RATE_OR_QUOTA_EXHAUSTED' ELSE NULL END",
                    (job,job))
            except Exception:
                failure_reason=None
        return {"id":job,"request":state["request"],
                "status":state["status"],
                "generation_on_hold":not self.generation_enabled(),
                "eligible_after":None,
                "next_stage":state.get("next_stage"),"completed_stages":list(outputs),
                "error_type":state.get("error_type"),"failure_reason":failure_reason,
                "retry_at":state.get("provider_wait_receipt",{}).get("retry_at"),
                "script":active_story.get("script",""),"scenes":scenes,"sources":sources,
                "photo_count":len(outputs.get("materials",{}).get("photos",[])),
                "voice_duration_ms":outputs.get("voice",{}).get("duration_ms"),
                "machine_pass":complete,
                "video_url":PREFIX+"/api/jobs/"+job+"/video" if complete else None,
                "video_sha256":outputs.get("render",{}).get("sha256") if complete else None,
                "source_revision":state["revision"]}

    def all_jobs(self):
        items=[]
        for record in self.entries():
            try:
                job=record["id"]
                detail=self.detail(job)
                items.append({"id":job,"request":detail["request"],
                              "status":detail["status"],"next_stage":detail["next_stage"],
                              "machine_pass":detail["machine_pass"]})
            except (OSError,ValueError,KeyError):
                items.append({"id":record["id"],"request":record["request"],
                              "status":"registration_pending","machine_pass":False})
        return items

    def video(self,job):
        detail=self.detail(job)
        if detail["machine_pass"] is not True:
            raise ValueError("video has not passed final audit")
        file=asset_path(self.root,"renders/"+safe_id(job)+"/final.mp4")
        with file.open("rb") as stream:
            observed=hashlib.file_digest(stream,"sha256").hexdigest()
        if observed!=detail["video_sha256"]:
            raise ValueError("MP4 changed since audited render")
        return file,"video/mp4"

    def photo(self,job,index):
        state=self.snapshot(safe_id(job))
        outputs=state.get("outputs",{})
        story=outputs.get("voice",{}).get("reviewed_story",outputs.get("story",{}))
        scenes=story.get("scenes",[])
        if not index.isdecimal() or int(index)>=len(scenes):
            raise ValueError("photo scene unavailable")
        asset_id=scenes[int(index)]["material_id"]
        asset=next((a for a in outputs.get("materials",{}).get("assets",[])
                    if a["id"]==asset_id),None)
        if asset is None:
            raise ValueError("photo not in verified corpus")
        validate_asset(self.root,asset)
        file=asset_path(self.root,asset["path"])
        mime=mimetypes.guess_type(file.name)[0] or ""
        if mime not in ("image/jpeg","image/webp","image/png"):
            raise ValueError("invalid photo type")
        return file,mime


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        protocol_version="HTTP/1.1"
        def log_message(self,*args):
            pass

        def reply(self,code,body,mime="application/json",extra=None,head=False):
            raw=(json.dumps(body,ensure_ascii=False).encode() if mime=="application/json"
                 else body if isinstance(body,bytes) else str(body).encode())
            self.send_response(code)
            self.send_header("Content-Type",mime)
            self.send_header("Content-Length",str(len(raw)))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("X-Frame-Options","DENY")
            if self.close_connection:
                self.send_header("Connection","close")
            for key,value in extra or ():
                self.send_header(key,value)
            self.end_headers()
            if not head:self.wfile.write(raw)

        def stream(self,file,mime,head=False):
            size=file.stat().st_size
            try:
                first,last,partial=byte_range(self.headers.get("Range"),size)
            except ValueError:
                self.reply(416,{"error":"invalid byte range"},head=head)
                return
            self.send_response(206 if partial else 200)
            self.send_header("Content-Type",mime)
            self.send_header("Accept-Ranges","bytes")
            self.send_header("Cache-Control","private, max-age=3600")
            self.send_header("Content-Length",str(last-first+1))
            self.send_header("X-Content-Type-Options","nosniff")
            if partial:self.send_header("Content-Range",f"bytes {first}-{last}/{size}")
            self.end_headers()
            if head:return
            with file.open("rb") as stream:
                stream.seek(first)
                remaining=last-first+1
                while remaining:
                    data=stream.read(min(65536,remaining))
                    if not data:break
                    self.wfile.write(data)
                    remaining-=len(data)

        def route_get(self,head=False):
            route=urlsplit(self.path).path
            if route in ("/healthz","/factory-next/healthz"):
                return self.reply(200,{"ok":True,"app":"factory-next-studio"},head=head)
            if route in (PREFIX,PREFIX+"/"):
                return self.reply(200,WEB.read_bytes(),"text/html; charset=utf-8",
                                  [("Content-Security-Policy","default-src 'self'; img-src 'self' https:; media-src 'self'; style-src 'unsafe-inline' 'self'; script-src 'unsafe-inline' 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'")],head=head)
            if route==PREFIX+"/api/status":
                return self.reply(200,app.public_status(),head=head)
            if route==PREFIX+"/api/jobs":
                return self.reply(200,app.all_jobs(),head=head)
            match=re.fullmatch(re.escape(PREFIX)+r"/api/jobs/([0-9a-f-]{36})(?:/(video|photo/\d+))?",route)
            if not match:
                return self.reply(404,{"error":"not found"},head=head)
            job,part=match.groups()
            if part=="video":
                file,mime=app.video(job)
                return self.stream(file,mime,head=head)
            if part and part.startswith("photo/"):
                file,mime=app.photo(job,part[6:])
                return self.stream(file,mime,head=head)
            return self.reply(200,app.detail(job),head=head)

        def do_HEAD(self):
            try:self.route_get(head=True)
            except (ValueError,KeyError,FileNotFoundError,OSError):
                self.reply(404,{"error":"not found"},head=True)

        def do_GET(self):
            try:self.route_get()
            except (ValueError,KeyError,FileNotFoundError,OSError):
                self.reply(404,{"error":"not found"})

        def do_POST(self):
            # Invalid JSON/Origin must never leave an unread request body on a
            # keep-alive connection: Caddy could interpret it as the next GET.
            self.close_connection=True
            path=urlsplit(self.path).path
            if path!=PREFIX+"/api/jobs":
                return self.reply(404,{"error":"not found"})
            if self.headers.get("Origin")!="https://studio.hodor.com.pl":
                return self.reply(403,{"error":"request must originate from Studio"})
            if self.headers.get("Content-Type","").split(";")[0]!="application/json":
                return self.reply(415,{"error":"JSON required"})
            try:
                length=int(self.headers.get("Content-Length",0))
                if length<2 or length>4096:
                    return self.reply(413,{"error":"bounded request required"})
                body=json.loads(self.rfile.read(length))
                result=app.create(body)
                return self.reply(201,result)
            except (ValueError,TypeError,KeyError):
                return self.reply(400,{"error":"check topic, language and duration"})
            except OverflowError as error:
                return self.reply(429,{"error":str(error)})
            except TTSBillingHold:
                return self.reply(503,{"error":"Google TTS: проверка отсутствия платных списаний не завершена; генерация приостановлена",
                                       "code":"GOOGLE_TTS_BILLING_UNVERIFIED"})
            except Exception:
                # Existing prepared or uncertain database operations are NOT retried.
                return self.reply(503,{"error":"registration incomplete; inspect saved job before retry"})

    return Handler


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=3003)
    parser.add_argument("--settings",default="/run/factory-v3/settings.json")
    parser.add_argument("--media-root",default="/data")
    args=parser.parse_args()
    revision=os.environ.get("FACTORY_V3_REVISION","")
    if not re.fullmatch("[a-f0-9]{40}",revision):
        raise ValueError("exact built source revision required")
    app=Studio(args.media_root,load_settings(args.settings),revision)
    server=ThreadingHTTPServer(("0.0.0.0",args.port),make_handler(app))
    server.serve_forever()


if __name__=="__main__":
    main()
