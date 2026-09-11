import asyncio
import base64
import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import edge_tts
from mutagen.mp3 import MP3

HOST = "0.0.0.0"
PORT = 3002
ALLOWED_VOICES = {
    "en-US-AndrewNeural",
    "pl-PL-MarekNeural",
    "ru-RU-DmitryNeural",
    "uk-UA-OstapNeural",
}

async def synthesize(text: str, voice: str) -> tuple[bytes, float]:
    chunks: list[bytes] = []
    communicate = edge_tts.Communicate(text=text, voice=voice)
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            chunks.append(chunk["data"])
    audio = b"".join(chunks)
    if not audio:
        raise RuntimeError("edge-tts returned no audio")
    duration = float(MP3(io.BytesIO(audio)).info.length)
    return audio, duration

class Handler(BaseHTTPRequestHandler):
    server_version = "ContentFactoryEdgeTTS/1.0"

    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)

    def _json(self, status: int, payload: dict):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok"})
            return
        if self.path == "/voices":
            self._json(200, {"voices": sorted(ALLOWED_VOICES)})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/synthesize":
            self._json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            text = body.get("text", "")
            voice = body.get("voice", "")
            if not isinstance(text, str) or not text.strip():
                self._json(400, {"error": "text_required"})
                return
            if voice not in ALLOWED_VOICES:
                self._json(400, {"error": "unsupported_voice", "voice": voice})
                return
            audio, duration = asyncio.run(synthesize(text.strip(), voice))
            self._json(200, {
                "audio_base64": base64.b64encode(audio).decode("ascii"),
                "audio_length": duration,
                "voice": voice,
            })
        except Exception as exc:
            self._json(500, {"error": "synthesis_failed", "message": str(exc)})

if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
