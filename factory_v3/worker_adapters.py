"""Single-attempt Google voice and existing exact-audio media-worker adapters."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid
from .http import JSONHTTP
from .preflight import asset_path, validate_asset

VOICES = {
    "en": ("en-US", "en-US-Chirp3-HD-Algenib"),
    "pl": ("pl-PL", "pl-PL-Chirp3-HD-Enceladus"),
    "ru": ("ru-RU", "ru-RU-Wavenet-D"),
    "uk": ("uk-UA", "uk-UA-Chirp3-HD-Enceladus"),
}
DENSITY = {15: 5, 30: 9, 45: 13, 60: 17}
WINDOWS = {15: (14208,15768),30:(28464,34000),45:(42864,46128),60:(58176,61656)}


def identity(job_id, kind, value):
    return str(uuid.uuid5(uuid.UUID(job_id), kind + ":" + value))


def probe_photo(path):
    result = subprocess.run(["ffprobe","-v","error","-show_streams","-of","json",str(path)],
                            check=True,capture_output=True,text=True,timeout=10)
    streams = json.loads(result.stdout)["streams"]
    if len(streams) != 1 or streams[0]["codec_type"] != "video" or streams[0]["codec_name"] not in {"mjpeg","png","webp"}:
        raise ValueError("selected photo must be a supported static image")
    return {"width": int(streams[0]["width"]), "height": int(streams[0]["height"])}


class VoiceDurationMismatch(ValueError):
    pass


class GoogleVoice:
    def __init__(self, access_token, http=None):
        self.access_token = access_token
        self.http = http or JSONHTTP()

    def synthesize(self, language, text):
        locale, voice = VOICES[language]
        response = self.http.request("POST", "https://texttospeech.googleapis.com/v1/text:synthesize",
            {"input":{"text":text},"voice":{"languageCode":locale,"name":voice},
             "audioConfig":{"audioEncoding":"MP3"}},
            {"Authorization":"Bearer "+self.access_token()}, timeout=60)
        encoded = response.get("audioContent")
        if not isinstance(encoded,str) or not encoded:
            raise ValueError("TTS returned no audio")
        raw = base64.b64decode(encoded,validate=True)
        if not raw:
            raise ValueError("TTS returned empty audio")
        return encoded, hashlib.sha256(raw).hexdigest()


class WorkerAdapters:
    def __init__(self, media_root, voice_provider, worker_url, audit, http=None, probe=probe_photo):
        self.root = Path(media_root).resolve()
        self.voice_provider = voice_provider
        self.worker_url = worker_url.rstrip("/")
        if self.worker_url != "http://shorts-v2-media-worker-1:3001":
            # Alternate endpoints must be injected explicitly for controlled tests.
            from urllib.parse import urlparse
            parsed = urlparse(self.worker_url)
            if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1","localhost","media-worker"}:
                raise ValueError("worker endpoint not allowlisted")
        self.audit = audit
        self.http = http or JSONHTTP()
        self.probe = probe

    def _post(self, path, payload, timeout=60):
        return self.http.request("POST", self.worker_url+path, payload, timeout=timeout)

    def _scene_inputs(self, job_id, payload):
        return [{"scene_uuid":identity(job_id,"scene",s["id"]), "scene_key":s["id"],
                 "narration":s["narration"]} for s in payload["scenes"]]

    def _stage_photos(self, job_id, payload):
        assets = {a["id"]:a for a in payload["assets"]}
        result = {}
        for scene in payload["scenes"]:
            asset = assets[payload["selection"][scene["id"]]]
            validate_asset(self.root,asset)
            source = asset_path(self.root,asset["path"])
            dimensions = self.probe(source)
            if dimensions["width"] <= 0 or dimensions["height"] <= 0:
                raise ValueError("invalid image dimensions")
            shot_id = identity(job_id,"shot",scene["id"])
            suffix = source.suffix.lower()
            if suffix not in {".jpg",".jpeg",".png",".webp"}:
                raise ValueError("unsupported selected photo extension")
            folder = self.root/"visuals"/str(uuid.UUID(job_id))/shot_id
            folder.mkdir(parents=True,exist_ok=False)
            selected = folder/("selected"+suffix)
            # Link immutable reviewed bytes, never download another image for render.
            os.link(source,selected)
            if hashlib.sha256(selected.read_bytes()).hexdigest()!=asset["sha256"]:
                raise ValueError("staged photo differs from reviewed bytes")
            result[scene["id"]] = {"path":str(selected),"shot_uuid":shot_id,
                "asset_sha256":asset["sha256"],"asset_width":dimensions["width"],
                "asset_height":dimensions["height"],"media_type":"photo",
                "visual_asset_id":identity(job_id,"asset",asset["sha256"])}
        return result

    def _validate_scene_count(self, payload):
        if len(payload["scenes"]) != DENSITY[payload["seconds"]]:
            raise ValueError("visual density does not match requested duration")

    def _duration_window(self, payload):
        return WINDOWS[payload["seconds"]]

    def voice(self, job_id, payload, outputs, before_send):
        self._validate_scene_count(payload)
        if re.search(r"(?:^|[.!?]\s+)(?:end|the end|koniec|конец|кінець)[.!?]*\s*$",
                     payload["script"],re.I):
            raise ValueError("standalone closing filler")
        staged = self._stage_photos(job_id,payload)
        before_send()
        encoded, expected_hash = self.voice_provider.synthesize(payload["language"],payload["script"])
        result = self._post("/voiceovers/"+job_id,{"audio_base64":encoded})
        if result.get("status")!="ready" or result.get("sha256")!=expected_hash:
            raise ValueError("stored voice differs from synthesized voice")
        low,high = self._duration_window(payload)
        if not low <= result["duration_ms"] <= high:
            raise VoiceDurationMismatch("voice duration outside accepted window; no re-synthesis")
        result["staged_photos"] = staged
        return result

    def align(self, job_id, payload, outputs):
        voice = outputs["voice"]
        result = self._post("/alignments/"+job_id,
            {"language_code":payload["language"],"narration":payload["script"],
             "audio_sha256":voice["sha256"],"audio_duration_ms":voice["duration_ms"],
             "scenes":self._scene_inputs(job_id,payload)}, timeout=330)
        expected = self._scene_inputs(job_id,payload)
        timings = result.get("scene_timings",[])
        if result.get("status")!="ready" or result.get("audio_sha256")!=voice["sha256"] or result.get("audio_duration_ms")!=voice["duration_ms"]:
            raise ValueError("alignment does not match exact voice")
        if result.get("global_coverage",0)<0.95 or len(timings)!=len(expected):
            raise ValueError("alignment coverage incomplete")
        for original,timing in zip(expected,timings):
            if timing.get("scene_uuid")!=original["scene_uuid"] or timing.get("scene_key")!=original["scene_key"]:
                raise ValueError("alignment scene identity changed")
        return result

    def render(self, job_id, payload, outputs):
        voice,alignment = outputs["voice"],outputs["align"]
        timings = alignment["scene_timings"]
        target = max(payload["seconds"]*1000,voice["duration_ms"])
        scenes = []
        for index,(scene,timing) in enumerate(zip(payload["scenes"],timings)):
            before = timings[index-1]["end_ms"] if index else 0
            start = (before+timing["start_ms"])//2 if index else 0
            end = (timing["end_ms"]+timings[index+1]["start_ms"])//2 if index+1<len(timings) else target
            photo = voice["staged_photos"][scene["id"]]
            scenes.append({"scene_uuid":timing["scene_uuid"],"scene_order":index+1,
                "segment_start_ms":start,"segment_end_ms":end,
                "speech_start_ms":timing["start_ms"],"speech_end_ms":timing["end_ms"],
                **{k:v for k,v in photo.items() if k!="path"},"asset_path":photo["path"]})
        result = self._post("/renders/"+job_id,
            {"input_audio_sha256":voice["sha256"],"audio_duration_ms":voice["duration_ms"],
             "requested_duration_ms":payload["seconds"]*1000,"target_duration_ms":target,
             "scenes":scenes}, timeout=600)
        if result.get("status")!="ready" or result.get("qa_passed") is not True or result.get("input_audio_sha256")!=voice["sha256"]:
            raise ValueError("renderer did not pass exact-audio machine QA")
        return result

    def qa(self, job_id, payload, outputs):
        result = self.audit(job_id,payload["seconds"],self.root)
        if result.get("passed") is not True or result.get("sha256")!=outputs["render"]["sha256"]:
            raise ValueError("actual final media audit failed")
        return {"status":"ready","machine_pass":True,"human_pass":False,**result}
