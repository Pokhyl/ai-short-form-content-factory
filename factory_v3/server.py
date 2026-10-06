"""Private owner UI; bounded single worker; no automatic recovery/retry."""
import argparse
import concurrent.futures
import hashlib
import hmac
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from uuid import UUID
from .runtime import Runtime, load_settings
from .preflight import asset_path, validate_asset

PREFIX = "/factory-v3"
STATIC = Path(__file__).parent / "web"


def identifier(value):
    return str(UUID(str(value)))


def byte_range(value, size):
    if not value:
        return 0, size - 1, False
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", value)
    if not match or not any(match.groups()):
        raise ValueError("invalid range")
    left, right = match.groups()
    if not left:
        length = int(right)
        if length <= 0:
            raise ValueError("invalid suffix")
        start, end = max(0, size-length), size-1
    else:
        start, end = int(left), int(right) if right else size-1
    end = min(end, size-1)
    if start < 0 or start >= size or end < start:
        raise ValueError("range unavailable")
    return start, end, True


class Sessions:
    def __init__(self, key):
        if not isinstance(key, str) or len(key) < 32:
            raise ValueError("separate private owner access token required")
        self.key = key.encode()

    def issue(self):
        body = str(int(time.time())) + ":" + secrets.token_hex(16)
        return body + ":" + hmac.new(self.key, body.encode(), hashlib.sha256).hexdigest()

    def valid(self, value):
        try:
            issued, nonce, signature = value.split(":")
            body = issued + ":" + nonce
            age = time.time() - int(issued)
            expected = hmac.new(self.key, body.encode(), hashlib.sha256).hexdigest()
            return 0 <= age <= 43200 and len(nonce) == 32 and hmac.compare_digest(expected, signature)
        except (ValueError, TypeError, AttributeError):
            return False


class Application:
    def __init__(self, runtime, origin):
        parsed = urlsplit(origin)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("exact HTTPS public origin required")
        self.origin = origin.rstrip("/")
        self.runtime = runtime
        self.sessions = Sessions(runtime.settings["owner_token"])
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="factory-v3")
        self.slots = threading.BoundedSemaphore(5)

    def submit(self, data):
        if set(data) != {"request_id", "topic", "language", "seconds"} or type(data["seconds"]) is not int:
            raise ValueError("only request identity, topic, language and duration allowed")
        request_id = identifier(data["request_id"])
        if not self.slots.acquire(blocking=False):
            raise OverflowError("queue full")
        try:
            result = self.runtime.create(request_id, data["topic"], data["language"], data["seconds"])
            if result["created"]:
                self.pool.submit(self._run, request_id)
                return result
        except BaseException:
            self.slots.release()
            raise
        self.slots.release()
        return result

    def _run(self, request_id):
        try:
            self.runtime.run(request_id)
        except Exception as error:
            # Do not expose HTTP bodies, tokens or stack traces; stage/call ledger holds evidence.
            try:
                prep = self.runtime.preparations.snapshot(request_id)
                if prep["status"] == "preparing":
                    self.runtime.preparations.reject(request_id, type(error).__name__)
            except Exception:
                pass
        finally:
            self.slots.release()

    def review(self, request_id):
        return self.runtime.ledger._call(
            "SELECT jsonb_build_object('decision',decision,'video_sha256',video_sha256,'comment',comment,'created_at',created_at) FROM factory_v3.human_reviews WHERE job_id=%s::uuid",
            (request_id,))

    def detail(self, request_id):
        request_id = identifier(request_id)
        status = self.runtime.status(request_id)
        review = self.review(request_id)
        status["review"] = review
        status["human_pass"] = False
        try:
            state = self.runtime.ledger.snapshot(request_id)
        except KeyError:
            return status
        payload = state["frozen"]["payload"]
        assets = {asset["id"]: asset for asset in payload["assets"]}
        status["script"] = payload["script"]
        status["sources"] = [
            {key: source.get(key, "") for key in ("id", "url", "title")}
            for source in payload.get("evidence", {}).get("sources", [])]
        status["scenes"] = []
        story = {s['id']: s for s in payload['scenes']}
        display = payload.get('visuals', payload['scenes'])
        render = state.get('outputs', {}).get('render', {})
        if payload.get('visuals') and render.get('segments'):
            display = [{'id': s['id'], 'material_id': s['material_id'],
                        'narration_scene_id': s['narration_scene_id']} for s in render['segments']]
        for visual in display:
            scene = story.get(visual.get('narration_scene_id'), visual)
            asset = assets[visual["material_id"] if payload.get("schema") == "material-first"
                           else payload["selection"][scene["id"]]]
            status["scenes"].append({
                "id": visual["id"], "narration": scene.get("narration", ""),
                "evidence_ids": scene.get("evidence_ids", []),
                "asset": {key: asset.get(key, "") for key in
                          ("source_url", "author", "license", "license_url", "license_version", "attribution", "sha256")}})
        if payload.get('visuals'):
            status['photo_count'] = len(payload['visuals'])
        if render.get('actual_duration_ms'):
            status['actual_duration_ms'] = render['actual_duration_ms']
        if state["status"] == "qa_pass":
            status["video_sha256"] = state["outputs"]["render"]["sha256"]
            status["human_pass"] = bool(review and review["decision"] == "accepted" and review["video_sha256"] == status["video_sha256"])
        return status

    def video(self, request_id):
        request_id = identifier(request_id)
        state = self.runtime.ledger.snapshot(request_id)
        if state["status"] != "qa_pass":
            raise ValueError("video has not passed machine QA")
        file = asset_path(self.runtime.root, "renders/" + request_id + "/final.mp4")
        expected = state["outputs"]["render"]["sha256"]
        with file.open("rb") as stream:
            observed = hashlib.file_digest(stream, "sha256").hexdigest()
        if observed != expected or observed != state["outputs"]["qa"]["sha256"]:
            raise ValueError("final video identity changed")
        return file, "video/mp4"

    def photo(self, request_id, scene_id):
        state = self.runtime.ledger.snapshot(identifier(request_id))
        payload = state["frozen"]["payload"]
        if payload.get("schema") == "material-first":
            selected = next(s["material_id"] for s in payload.get("visuals", payload["scenes"]) if s["id"] == scene_id)
        else:
            selected = payload["selection"][scene_id]
        asset = next(a for a in payload["assets"] if a["id"] == selected)
        validate_asset(self.runtime.root, asset)
        file = asset_path(self.runtime.root, asset["path"])
        mime = mimetypes.guess_type(file.name)[0]
        if mime not in {"image/jpeg", "image/png", "image/webp"}:
            raise ValueError("unsupported photo")
        return file, mime

    def record_review(self, request_id, data):
        request_id = identifier(request_id)
        if set(data) != {"decision", "video_sha256", "comment"} or data["decision"] not in {"accepted", "rejected"}:
            raise ValueError("explicit decision required")
        if not isinstance(data["comment"], str) or len(data["comment"]) > 2000:
            raise ValueError("bounded comment required")
        file, _ = self.video(request_id)
        with file.open("rb") as stream:
            observed = hashlib.file_digest(stream, "sha256").hexdigest()
        if data["video_sha256"] != observed:
            raise ValueError("review targets a different video")
        self.runtime.ledger._call(
            "INSERT INTO factory_v3.human_reviews(job_id,video_sha256,decision,comment) VALUES(%s::uuid,%s,%s,%s) ON CONFLICT(job_id) DO NOTHING RETURNING job_id",
            (request_id, observed, data["decision"], data["comment"]))
        saved = self.review(request_id)
        if any(saved[key] != data[key] for key in ("video_sha256", "decision", "comment")):
            raise ValueError("existing decision is immutable")
        return saved


def handler(application):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass  # Paths/bodies/headers may contain private material.

        def reply(self, code, body=b"", mime="application/json", extra=None):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self'; media-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            for key, value in (extra or {}).items():
                self.send_header(key, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def authenticated(self):
            cookie = SimpleCookie()
            try:
                cookie.load(self.headers.get("Cookie", ""))
                return application.sessions.valid(cookie["factory_v3_session"].value)
            except (KeyError, ValueError):
                return False

        def body(self):
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 8192 or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("bounded JSON body required")
            value = json.loads(self.rfile.read(length))
            if not isinstance(value, dict):
                raise ValueError("JSON object required")
            return value

        def media(self, file, mime):
            size = file.stat().st_size
            try:
                start, end, partial = byte_range(self.headers.get("Range"), size)
            except ValueError:
                self.reply(416, extra={"Content-Range": "bytes */" + str(size)})
                return
            self.send_response(206 if partial else 200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(end-start+1))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "private, no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if partial:
                self.send_header("Content-Range", "bytes " + str(start) + "-" + str(end) + "/" + str(size))
            self.end_headers()
            if self.command != "HEAD":
                with file.open("rb") as stream:
                    stream.seek(start)
                    remaining = end-start+1
                    while remaining:
                        chunk = stream.read(min(65536, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)

        def dispatch(self):
            path = urlsplit(self.path).path
            if not path.startswith(PREFIX + "/") and path != PREFIX:
                self.reply(404, {"error": "not_found"})
                return
            local = path[len(PREFIX):] or "/"
            if self.command in {"GET", "HEAD"}:
                static = {"/": ("index.html", "text/html; charset=utf-8"),
                          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                          "/style.css": ("style.css", "text/css; charset=utf-8")}
                if local in static:
                    name, mime = static[local]
                    self.reply(200, (STATIC/name).read_bytes(), mime)
                    return
                if local == "/health":
                    self.reply(200, {"status": "serving", "project_ready": False, "source_revision": application.runtime.revision})
                    return
            if self.command == "POST" and self.headers.get("Origin") != application.origin:
                self.reply(403, {"error": "origin_rejected"})
                return
            if local == "/api/session" and self.command == "POST":
                data = self.body()
                token = data.get("token")
                if set(data) != {"token"} or not isinstance(token, str) or not hmac.compare_digest(token, application.runtime.settings["owner_token"]):
                    self.reply(401, {"error": "access_denied"})
                    return
                cookie = "factory_v3_session=" + application.sessions.issue() + "; Path=" + PREFIX + "; HttpOnly; Secure; SameSite=Strict; Max-Age=43200"
                self.reply(200, {"authenticated": True}, extra={"Set-Cookie": cookie})
                return
            if not self.authenticated():
                self.reply(401, {"error": "authentication_required"})
                return
            parts = local.strip("/").split("/")
            if local == "/api/session" and self.command == "GET":
                self.reply(200, {"authenticated": True})
            elif local == "/api/requests" and self.command == "POST":
                result = application.submit(self.body())
                self.reply(202 if result["created"] else 200, result)
            elif local == "/api/requests" and self.command == "GET":
                result = application.runtime.ledger._call(
                    "SELECT COALESCE(jsonb_agg(x ORDER BY x.created_at DESC),'[]'::jsonb) FROM (SELECT p.id,p.request,p.created_at,COALESCE(j.status,p.status) AS status FROM factory_v3.preparations p LEFT JOIN factory_v3.jobs j ON j.id=p.id ORDER BY p.created_at DESC LIMIT 50) x", ())
                self.reply(200, result)
            elif len(parts) == 3 and parts[:2] == ["api", "requests"] and self.command == "GET":
                self.reply(200, application.detail(parts[2]))
            elif len(parts) == 4 and parts[:2] == ["api", "requests"] and parts[3] == "review" and self.command == "POST":
                self.reply(200, application.record_review(parts[2], self.body()))
            elif len(parts) == 2 and parts[0] == "video" and self.command in {"GET", "HEAD"}:
                self.media(*application.video(parts[1]))
            elif len(parts) == 3 and parts[0] == "photo" and self.command in {"GET", "HEAD"}:
                self.media(*application.photo(parts[1], parts[2]))
            else:
                self.reply(404, {"error": "not_found"})

        def do_GET(self):
            self.safe_dispatch()
        def do_HEAD(self):
            self.safe_dispatch()
        def do_POST(self):
            self.safe_dispatch()

        def safe_dispatch(self):
            try:
                self.dispatch()
            except (BrokenPipeError, ConnectionResetError):
                pass
            except OverflowError:
                self.reply(429, {"error": "queue_full"})
            except KeyError:
                self.reply(404, {"error": "not_found"})
            except (ValueError, TypeError, StopIteration):
                self.reply(409, {"error": "request_rejected"})
            except Exception:
                self.reply(503, {"error": "temporarily_unavailable"})
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", default="/run/factory-v3/settings.json")
    parser.add_argument("--media-root", default="/data")
    parser.add_argument("--port", type=int, default=3002)
    args = parser.parse_args()
    settings = load_settings(args.settings)
    runtime = Runtime(settings, args.media_root, os.environ.get("FACTORY_V3_REVISION", ""))
    application = Application(runtime, settings["public_origin"])
    server = ThreadingHTTPServer(("0.0.0.0", args.port), handler(application))
    try:
        server.serve_forever()
    finally:
        server.server_close()
        application.pool.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    main()
