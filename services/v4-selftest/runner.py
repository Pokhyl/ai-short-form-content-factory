from __future__ import annotations
import asyncio, hashlib, json, re, shutil, subprocess, sys, threading, traceback, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import edge_tts
from faster_whisper import WhisperModel

RUNTIME_ROOT=Path("/opt/ai-short-form-v4-runtime"); ROOT=Path("/opt/ai-short-form-v4-selftest")
JOBS=ROOT/"jobs"; CACHE=ROOT/"cache"/"commons"; TOKEN=(ROOT/"model_gateway_token").read_text().strip()
MODEL_URL="http://127.0.0.1:5678/webhook/v4-model-gateway"; SEARX="http://127.0.0.1:8888/search"
STUDIO=Path("/opt/ai-short-form-content-factory/studio/v4-media"); REMOTION=ROOT/"remotion-runtime"
NODE_MODULES=Path("/opt/ai-short-form-v4-upstreams/OpenMontage/remotion-composer/node_modules")
def _env_value(path,key):
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(key+"="):
                return line.split("=",1)[1].strip()
    except Exception:
        pass
    return ""
PEXELS_KEY=_env_value("/opt/ai-short-form-content-factory/.env","PEXELS_API_KEY")
VOICES={"en":"en-US-AndrewNeural","pl":"pl-PL-MarekNeural","ru":"ru-RU-DmitryNeural","uk":"uk-UA-OstapNeural"}
LANG={"en":"English","pl":"Polish","ru":"Russian","uk":"Ukrainian"}; WORDS={15:"30-40",30:"60-75",45:"90-110",60:"120-145"}; SHOT_RANGE={15:(5,7),30:(8,10),45:(10,12),60:(12,14)}; SHOTS={k:f"{v[0]}-{v[1]}" for k,v in SHOT_RANGE.items()}
sys.path.insert(0,str(RUNTIME_ROOT))
from prototype.v4.schema import parse_director_payload
from prototype.v4.timeline_builder import compile_segment_timeline, sha256_file
from prototype.v4.timeline_contract import validate_timeline_payload
from prototype.v4.commons_media import search_commons_candidates, materialize_commons_candidate
from prototype.v4.asset_resolver import resolve_timeline_assets
from prototype.v4.render_manifest import assemble_render_manifest
from prototype.v4.render_bundle import stage_render_bundle
from prototype.v4.selftest_director_contract import normalize_director_visual_contract as normalize_selftest_director_visual_contract, validate_director_shot_contract
from prototype.v4.selftest_media_contract import parse_media_selections
JOBS.mkdir(parents=True,exist_ok=True); CACHE.mkdir(parents=True,exist_ok=True); STUDIO.mkdir(parents=True,exist_ok=True)
JOB_LOCK=threading.Lock(); WHISPER_LOCK=threading.Lock(); _WHISPER=None

def now(): return datetime.now(timezone.utc).isoformat()
def dump(p,o): Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def jd(j): return JOBS/j
def sp(j): return jd(j)/"status.json"
def status(j,**kw):
    s=load(sp(j)) if sp(j).exists() else {"job_id":j,"created_at":now()}; s.update(kw); s["updated_at"]=now(); dump(sp(j),s); return s

def parse_json_text(t):
    t=(t or "").strip()
    if t.startswith("```"):
        x=t.splitlines()[1:]; x=x[:-1] if x and x[-1].strip()=="```" else x; t="\n".join(x).strip()
    return json.loads(t)

def model_json(prompt,temp=.15):
    r=requests.post(MODEL_URL,headers={"Content-Type":"application/json","X-V4-Internal-Key":TOKEN},json={"mode":"director","prompt":prompt,"temperature":temp},timeout=90); r.raise_for_status()
    text=str(r.json().get("text") or "").strip()
    if not text: raise RuntimeError("model gateway returned empty text")
    return parse_json_text(text)

def research_query(topic):
    q=str(topic or "").strip()
    if not q: raise ValueError("no research query")
    return q

def search_sources(q):
    r=requests.get(SEARX,params={"q":q,"format":"json","language":"all","safesearch":0},timeout=30); r.raise_for_status(); rows=r.json().get("results") or []
    blocked=("youtube.com","youtu.be","facebook.com","instagram.com","tiktok.com","pinterest.","x.com","twitter.com","reddit.com")
    out=[]; seen=set()
    for x in rows:
        u=str(x.get("url") or "").strip(); host=(urlparse(u).hostname or "").lower()
        if not u.startswith(("http://","https://")) or not host or any(b in host for b in blocked): continue
        key=host+urlparse(u).path
        if key in seen: continue
        seen.add(key); out.append({"title":str(x.get("title") or ""),"url":u,"snippet":str(x.get("content") or "")})
        if len(out)>=8: break
    if len(out)<3: raise RuntimeError(f"research returned only {len(out)} sources")
    return out

def evidence(rows):
    out=[]; h={"User-Agent":"ai-short-form-content-factory-v4-selftest/1.0"}
    for x in rows:
        text=""
        try:
            r=requests.get(x["url"],headers=h,timeout=12,allow_redirects=True); ct=r.headers.get("content-type","").lower()
            if r.ok and ("text/html" in ct or "text/plain" in ct):
                s=BeautifulSoup(r.text,"html.parser")
                for tag in s(["script","style","noscript","svg"]): tag.decompose()
                text=" ".join(s.stripped_strings)
        except Exception: pass
        ex=(text[:1800] if text else x["snippet"][:900]).strip()
        if ex: out.append({"title":x["title"],"url":x["url"],"excerpt":ex})
        if len(out)>=4: break
    if len(out)<3: raise RuntimeError(f"could fetch only {len(out)} evidence sources")
    return out

def director_prompt(topic,language,duration,ev):
    return f"""Return ONE raw JSON object only. You are a factual short-form vertical-video director.
Topic: {topic}
Language: {language} ({LANG[language]}). Target duration: about {duration} seconds.
Use ONLY EVIDENCE below for facts and only those exact URLs in facts.source_urls. Do not invent sources.
Narration target: {WORDS[duration]} spoken words. Write natural speech-ready {LANG[language]}. Spell numbers, units and ambiguous abbreviations as ordinary spoken words. Do not put raw digits or unit abbreviations in spoken narration.
Create a small semantic scene structure, usually 3-6 scenes. First scene purpose is hook. Scene narrations joined with one space MUST exactly equal spoken_script. Semantic scenes are meaning structure, NOT editing shots.
Each scene contains shots. Use at least {SHOT_RANGE[duration][0]} total shots; {SHOTS[duration]} is the normal target, but semantic pacing may justify more. Do NOT collapse to one shot per semantic scene. Each shot narration is a contiguous piece of its scene narration; shot narrations joined with one space MUST exactly equal scene narration.
Choose shot visual_mode from exact_media or stock. Stock is allowed ONLY for genuinely contextual hook/example/transition shots where ordinary real-world footage communicates the idea. Explain/proof/mechanism shots MUST use exact_media: the actual subject or a truthful technical diagram/photo from Wikimedia Commons. Never use generic lifestyle stock as factual fallback.
For exact_media shots provide a concise English Wikimedia Commons query for a concrete visible entity/object/place/photo/diagram likely to exist in Commons. For stock shots provide a concise English Pexels query. must_show MUST name concrete visible content, never placeholders such as subject/object or an invisible abstract concept unless a truthful diagram visibly depicts it. Text is overlay only, never the primary visual.
Schema: {{"topic":"...","language":"{language}","target_seconds":{duration},"hook":"...","spoken_script":"...","facts":[{{"fact_id":"F1","claim":"...","source_urls":["exact evidence URL"]}}],"scenes":[{{"scene_id":"S1","narration":"...","purpose":"hook|explain|proof|example|transition|close","visual_mode":"exact_media|stock","visual_query":"English query","must_show":["subject"],"must_not_show":["misleading substitute"],"source_refs":["F1"],"on_screen_text":null,"shots":[{{"shot_id":"S1A","narration":"exact narration piece","visual_mode":"exact_media|stock","visual_query":"English provider query","must_show":["subject"],"must_not_show":["misleading substitute"]}}]}}]}}
EVIDENCE: {json.dumps(ev,ensure_ascii=False)}"""

def _semantic_fingerprint(raw):
    return {
        "topic":raw.get("topic"), "language":raw.get("language"), "target_seconds":raw.get("target_seconds"),
        "hook":raw.get("hook"), "spoken_script":raw.get("spoken_script"), "facts":raw.get("facts"),
        "scenes":[{"scene_id":s.get("scene_id"),"narration":s.get("narration"),"purpose":s.get("purpose"),"source_refs":s.get("source_refs"),"on_screen_text":s.get("on_screen_text")} for s in raw.get("scenes",[])],
    }

def director_correction_prompt(raw,duration,error):
    return f"""Return ONE raw JSON object only. Correct ONLY the editing-shot structure of this V4 director plan.
The semantic content is frozen: do not change topic, language, target_seconds, hook, spoken_script, facts, source URLs, scene count/order/IDs, scene narration, purpose, source_refs or on_screen_text.
You MAY change scene visual_mode/visual_query/must_show/must_not_show so they summarize the corrected shots.
You MUST rewrite shots[] as the editing layer. Use at least {SHOT_RANGE[duration][0]} total shots; {SHOTS[duration]} is the normal target, but semantic pacing may justify more. Do not collapse to one shot per semantic scene. Each shot narration must be a contiguous piece of its scene narration, and joined shot narrations must reconstruct that scene narration exactly.
Allowed shot visual_mode: exact_media or stock. Stock is allowed ONLY for hook/example/transition. Explain/proof/close factual shots must use exact_media showing the actual subject or a truthful technical diagram/photo from Wikimedia Commons. Never use generic lifestyle stock as factual fallback.
For exact_media use concise English Wikimedia Commons queries for concrete visible entities/objects/places/photos/diagrams likely to exist in Commons. For stock use concise English Pexels queries. Every shot needs non-empty must_show and must_not_show. must_show must name concrete visible content, never placeholders such as subject/object or an invisible abstract concept unless a truthful diagram visibly depicts it.
Validation error to correct: {error}
ORIGINAL DIRECTOR: {json.dumps(raw,ensure_ascii=False)}"""


def normalize_director_visual_contract(raw):
    return normalize_selftest_director_visual_contract(raw)

def validate_director_correction(before,after):
    if _semantic_fingerprint(before)!=_semantic_fingerprint(after):
        raise ValueError("shot correction changed frozen semantic content")

def validate_director(raw,ev,duration):
    plan=parse_director_payload(raw); allowed={x["url"] for x in ev}
    for f in plan.facts:
        for u in f.source_urls:
            if u not in allowed: raise ValueError(f"unverified fact URL: {u}")
    validate_director_shot_contract(raw,duration)
    return plan

def whisper_model():
    global _WHISPER
    with WHISPER_LOCK:
        if _WHISPER is None: _WHISPER=WhisperModel("small",device="cpu",compute_type="int8")
        return _WHISPER

def synth(script,language,path):
    async def go(): await edge_tts.Communicate(script,VOICES[language]).save(str(path))
    asyncio.run(go())
    if not path.exists() or path.stat().st_size==0: raise RuntimeError("TTS produced no audio")

def transcribe(audio,out):
    segs=[]; words=[]; segments,info=whisper_model().transcribe(str(audio),beam_size=5,word_timestamps=True,vad_filter=False)
    for s in segments:
        segs.append({"start":round(float(s.start),3),"end":round(float(s.end),3),"text":str(s.text).strip()})
        for w in (s.words or []): words.append({"start":round(float(w.start),3),"end":round(float(w.end),3),"word":str(w.word).strip()})
    duration=max([x["end"] for x in words] or [0]); data={"language":info.language,"probability":round(float(info.language_probability),6),"duration":round(duration,3),"segments":segs,"words":words}; dump(out,data); return data

def pexels_candidates(q):
    if not PEXELS_KEY: raise RuntimeError("Pexels API key is not configured")
    r=requests.get("https://api.pexels.com/v1/search",headers={"Authorization":PEXELS_KEY},params={"query":q,"orientation":"portrait","per_page":8},timeout=30); r.raise_for_status()
    out=[]
    for x in (r.json().get("photos") or []):
        w=int(x.get("width") or 0); h=int(x.get("height") or 0); u=str((x.get("src") or {}).get("original") or "")
        if not u or w<=0 or h<=0: continue
        out.append({"provider":"pexels","file_title":f"Pexels:{x.get('id')}","page_url":str(x.get("url") or ""),"download_url":u,"selected_width":w,"selected_height":h,"orientation":"portrait" if h>w else ("landscape" if w>h else "square"),"license":"Pexels License","license_url":"https://www.pexels.com/license/","artist":str(x.get("photographer") or ""),"credit":str(x.get("photographer") or ""),"description":str(x.get("alt") or q),"attribution_required":False})
    return out

def materialize_pexels(candidate,output_dir):
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); fid=str(candidate["file_title"]).replace(":","-"); path=out/(fid+".jpg")
    h=hashlib.sha256(); total=0
    with requests.get(candidate["download_url"],stream=True,timeout=60) as r:
        r.raise_for_status()
        with path.open("wb") as f:
            for chunk in r.iter_content(1024*1024):
                if not chunk: continue
                f.write(chunk); h.update(chunk); total+=len(chunk)
    if total<=0: raise RuntimeError("Pexels download produced empty file")
    m=dict(candidate); m.update({"local_path":str(path),"bytes":total,"sha256":h.hexdigest()}); mp=path.with_suffix(path.suffix+".json"); dump(mp,m); m["metadata_path"]=str(mp); return m

def choose_prompt(rows):
    data=[]
    for r in rows:
        data.append({"shot_id":r["shot_id"],"visual_mode":r["visual_mode"],"query":r["query"],"must_show":r["must_show"],"must_not_show":r["must_not_show"],"candidates":[{"provider":c.get("provider"),"file_title":c["file_title"],"description":c.get("description","")[:500],"orientation":c.get("orientation")} for c in r["candidates"]]})
    return "Return ONE raw JSON object only with this exact shape: {\"selections\":{\"S1A\":\"exact file_title from candidates or null\"}}. Include every shot_id exactly once. Choose only a candidate that specifically satisfies must_show and avoids must_not_show. If none is truthful, use null. DATA: "+json.dumps(data,ensure_ascii=False)

def build_visuals(raw,d):
    rows=[]
    for sc in raw["scenes"]:
        purpose=str(sc.get("purpose") or "")
        for sh in sc["shots"]:
            sid=str(sh["shot_id"]); q=str(sh["visual_query"]).strip(); mode=str(sh.get("visual_mode") or sc.get("visual_mode") or "exact_media")
            if mode=="stock":
                if purpose not in {"hook","example","transition"}: raise RuntimeError(f"contextual stock forbidden for {purpose} shot {sid}")
                cs=pexels_candidates(q)
            else:
                cs=[c for c in search_commons_candidates(q,limit=12,max_width=1440,cache_dir=CACHE) if str(c.get("mime") or "").startswith("image/")][:6]
            if not cs: raise RuntimeError(f"no provider media for {sid}: {q}")
            rows.append({"shot_id":sid,"visual_mode":mode,"purpose":purpose,"query":q,"must_show":sh.get("must_show",[]),"must_not_show":sh.get("must_not_show",[]),"candidates":cs})
    pick_payload=model_json(choose_prompt(rows),.05); dump(d/"media-selection.json",pick_payload); picks=parse_media_selections(pick_payload,[r["shot_id"] for r in rows]); by={r["shot_id"]:r for r in rows}; amap={}; obs=[]; selected={}; media=d/"media"; media.mkdir(exist_ok=True)
    for sc in raw["scenes"]:
        osh=[]
        for sh in sc["shots"]:
            sid=str(sh["shot_id"]); row=by[sid]; title=picks.get(sid)
            if not title: raise RuntimeError(f"no truthful media selected for {sid}")
            m=[c for c in row["candidates"] if c["file_title"]==title]
            if len(m)!=1: raise RuntimeError(f"invalid media selection for {sid}")
            cand=m[0]; meta=materialize_pexels(cand,media/sid) if cand.get("provider")=="pexels" else materialize_commons_candidate(cand,media/sid)
            selected[sid]=meta; amap[sid]=meta["metadata_path"]; o=meta["orientation"]
            if row["visual_mode"]=="stock":
                pv={"mode":"justified_context","kind":"photo","source_class":"contextual","visible_subject":"; ".join(sh.get("must_show") or []),"layout":"fullscreen" if o=="portrait" else "contain","source_orientation":o,"context_justification":f"Contextual {row['purpose']} shot directly showing: "+"; ".join(sh.get("must_show") or [])}
            else:
                pv={"mode":"exact_media","kind":"photo","source_class":"exact","visible_subject":"; ".join(sh.get("must_show") or []),"layout":"fullscreen" if o=="portrait" else "contain","source_orientation":o,"expected_file_title":meta["file_title"]}
            osh.append({"shot_id":sid,"narration":sh["narration"],"primary_visual":pv,"overlays":[{"type":"caption"}]})
        obs.append({"beat_id":sc["scene_id"],"narration":sc["narration"],"primary_visual":osh[0]["primary_visual"],"overlays":[{"type":"caption"}],"shots":osh})
    dump(d/"visual-obligations.json",obs); dump(d/"asset-map.json",amap); dump(d/"selected-media.json",selected); return obs,amap

def render(bundle,out):
    out.mkdir(parents=True,exist_ok=True)
    cmd=["docker","run","--rm","--shm-size=1g","-v",f"{REMOTION}:/app","-v",f"{NODE_MODULES}:/app/node_modules","-v",f"{bundle}:/bundle:ro","-v",f"{out}:/out","ai-short-form-v4-remotion:1","./node_modules/.bin/remotion","render","src/index.tsx","VerticalShort","/out/video.mp4","--props=/bundle/props.json","--public-dir=/bundle/public","--concurrency=1","--log=error"]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=1200); (out/"render.log").write_text((p.stdout or "")+"\n"+(p.stderr or ""),encoding="utf-8")
    if p.returncode: raise RuntimeError(f"Remotion failed: {p.returncode}")
    v=out/"video.mp4"
    if not v.exists() or v.stat().st_size<100000: raise RuntimeError("invalid rendered MP4")
    pc=["docker","run","--rm","-v",f"{out}:/out:ro","ai-short-form-v4-remotion:1","ffprobe","-v","error","-show_entries","stream=codec_name,width,height,sample_rate,channels","-show_entries","format=duration,size","-of","json","/out/video.mp4"]
    q=subprocess.run(pc,capture_output=True,text=True,timeout=60,check=True); return v,json.loads(q.stdout)

def run_job(j):
    with JOB_LOCK:
        d=jd(j)
        try:
            req=load(d/"request.json"); topic=req["topic"]; language=req["language"]; duration=req["duration"]
            status(j,state="running",stage="research_query",progress=5,message="Building research query"); q=research_query(topic); dump(d/"research-query.json",{"query":q})
            status(j,stage="research",progress=12,message="Searching public web sources"); sr=search_sources(q); dump(d/"search-results.json",sr); ev=evidence(sr); dump(d/"evidence.json",ev)
            status(j,stage="director",progress=24,message="Building factual multishot storyboard"); raw_model=model_json(director_prompt(topic,language,duration,ev),.15); dump(d/"director-raw.json",raw_model); raw=normalize_director_visual_contract(raw_model); dump(d/"director-initial.json",raw)
            try:
                plan=validate_director(raw,ev,duration)
            except ValueError as first_error:
                status(j,stage="director_shots",progress=28,message=f"Correcting editing-shot contract: {first_error}")
                corrected=model_json(director_correction_prompt(raw,duration,str(first_error)),.05); corrected=normalize_director_visual_contract(corrected); dump(d/"director-corrected.json",corrected); validate_director_correction(raw,corrected); raw=corrected; plan=validate_director(raw,ev,duration)
            dump(d/"director.json",raw); script=plan.spoken_script; (d/"script.txt").write_text(script,encoding="utf-8")
            status(j,stage="tts",progress=34,message="Generating continuous narration"); audio=d/"voice.mp3"; synth(script,language,audio)
            status(j,stage="whisper",progress=44,message="Aligning exact audio"); wh=transcribe(audio,d/"whisper.json")
            status(j,stage="media",progress=56,message="Finding exact free media"); obs,amap=build_visuals(raw,d)
            status(j,stage="timeline",progress=70,message="Compiling semantic shot timeline"); tl=compile_segment_timeline(whisper_payload=wh,visual_obligations=obs,script_text=script,audio_sha256=sha256_file(audio)); validate_timeline_payload(tl); dump(d/"timeline.json",tl); res=resolve_timeline_assets(tl,amap); dump(d/"resolved-timeline.json",res); man=assemble_render_manifest(res,wh,audio_path=audio); dump(d/"render-manifest.json",man); bundle=d/"render-bundle"; stage_render_bundle(man,bundle)
            status(j,stage="render",progress=82,message="Rendering vertical MP4"); video,probe=render(bundle,d/"out"); sha=hashlib.sha256(video.read_bytes()).hexdigest(); public=STUDIO/f"{j}.mp4"; shutil.copy2(video,public); dump(d/"probe.json",probe)
            status(j,state="complete",stage="complete",progress=100,message="Ready for review",result_url=f"/v4-media/{j}.mp4",sha256=sha,probe=probe,acceptance="machine_rendered")
        except Exception as e:
            (d/"error.log").write_text(traceback.format_exc(),encoding="utf-8"); status(j,state="failed",stage="failed",message=str(e),error=str(e))

def create(payload):
    topic=str(payload.get("topic") or "").strip(); language=str(payload.get("language") or "").strip().lower()
    try: duration=int(payload.get("duration"))
    except Exception: duration=0
    if not topic or len(topic)>300: raise ValueError("topic is required and <= 300 chars")
    if language not in VOICES: raise ValueError("language must be en/pl/ru/uk")
    if duration not in (15,30,45,60): raise ValueError("duration must be 15/30/45/60")
    j=str(uuid.uuid4()); d=jd(j); d.mkdir(parents=True); dump(d/"request.json",{"topic":topic,"language":language,"duration":duration}); status(j,state="queued",stage="queued",progress=0,message="Queued",topic=topic,language=language,duration=duration); threading.Thread(target=run_job,args=(j,),daemon=True).start(); return load(sp(j))

def listing():
    a=[]
    for p in JOBS.glob("*/status.json"):
        try:a.append(load(p))
        except:pass
    return sorted(a,key=lambda x:x.get("created_at",""),reverse=True)[:30]

class H(BaseHTTPRequestHandler):
    def sendj(self,c,x):
        b=json.dumps(x,ensure_ascii=False).encode(); self.send_response(c); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p=self.path.split("?",1)[0]
        if p=="/health": return self.sendj(200,{"ok":True,"service":"v4-selftest"})
        if p=="/jobs": return self.sendj(200,{"jobs":listing()})
        m=re.fullmatch(r"/jobs/([0-9a-f-]{36})",p)
        if m: return self.sendj(200,load(sp(m.group(1)))) if sp(m.group(1)).exists() else self.sendj(404,{"error":"not_found"})
        return self.sendj(404,{"error":"not_found"})
    def do_POST(self):
        if self.path.split("?",1)[0]!="/jobs": return self.sendj(404,{"error":"not_found"})
        try:
            n=int(self.headers.get("Content-Length","0")); return self.sendj(201,create(json.loads(self.rfile.read(n) or b"{}")))
        except ValueError as e:return self.sendj(400,{"error":"invalid_input","message":str(e)})
        except Exception as e:return self.sendj(500,{"error":"server_error","message":str(e)})
    def log_message(self,*a): pass

if __name__=="__main__": ThreadingHTTPServer(("172.18.0.1",8094),H).serve_forever()
