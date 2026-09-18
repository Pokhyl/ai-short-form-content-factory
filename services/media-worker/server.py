#!/usr/bin/env python3
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data")).resolve()
PORT = int(os.environ.get("PORT", "3001"))
USER_AGENT = os.environ.get(
    "WIKIMEDIA_USER_AGENT",
    "AIShortFormContentFactory/2.0 (https://publisher.hodor.com.pl)",
)
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

STOPWORDS = {
    "the","and","for","with","from","into","that","this","these","those","why","how",
    "are","was","were","is","of","to","in","on","a","an","as","at","by","or","about",
}
BAD_VISUAL_TERMS = {"logo","icon","flag","coat of arms","screenshot","map"}

class BuildError(Exception):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code = code
        self.status = status

def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        tail = p.stderr[-3000:].replace("\n", " ")
        raise BuildError("media_command_failed", f"{cmd[0]} failed: {tail}", 500)
    return p.stdout

def safe_data_path(path_text):
    p = Path(path_text).resolve()
    try:
        p.relative_to(DATA_DIR)
    except ValueError:
        raise BuildError("invalid_path", "path must stay inside /data")
    return p

def clean_html(value):
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(value))
    return " ".join(html.unescape(text).split())

def words(text):
    return re.findall(r"[A-Za-zÀ-žА-Яа-яІіЇїЄєҐґ0-9]+", text.lower())

def query_tokens(text):
    return {w for w in words(text) if len(w) >= 3 and w not in STOPWORDS}

def extmeta_value(meta, key):
    v = (meta or {}).get(key)
    if isinstance(v, dict):
        return clean_html(v.get("value"))
    return ""

def commons_candidates(query):
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": "12",
        "prop": "imageinfo",
        "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": "1600",
    }
    url = COMMONS_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            payload = json.load(r)
    except Exception as e:
        raise BuildError("wikimedia_request_failed", str(e), 502)

    out = []
    for page in payload.get("query", {}).get("pages", []):
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        mime = str(info.get("mime") or "")
        width = int(info.get("width") or 0)
        height = int(info.get("height") or 0)
        if mime not in {"image/jpeg", "image/png", "image/webp"}:
            continue
        if width < 640 or height < 480:
            continue
        meta = info.get("extmetadata") or {}
        out.append({
            "pageid": page.get("pageid"),
            "title": page.get("title") or "",
            "mime": mime,
            "width": width,
            "height": height,
            "url": info.get("thumburl") or info.get("url"),
            "original_url": info.get("url"),
            "description": extmeta_value(meta, "ImageDescription"),
            "artist": extmeta_value(meta, "Artist"),
            "credit": extmeta_value(meta, "Credit"),
            "license": extmeta_value(meta, "LicenseShortName"),
            "license_url": extmeta_value(meta, "LicenseUrl"),
        })
    return out

def visual_score(candidate, query):
    q = query_tokens(query)
    title_tokens = query_tokens(candidate["title"])
    desc_tokens = query_tokens(candidate["description"])
    hay = title_tokens | desc_tokens

    title_overlap = len(q & title_tokens)
    total_overlap = len(q & hay)
    score = title_overlap * 24 + max(0, total_overlap - title_overlap) * 10

    if candidate["mime"] == "image/jpeg":
        score += 6
    if candidate["width"] >= 1200:
        score += 3
    if candidate["height"] >= 800:
        score += 2

    candidate_low = (candidate["title"] + " " + candidate["description"]).lower()
    query_low = query.lower()

    for term in BAD_VISUAL_TERMS:
        if term in candidate_low and term not in query_low:
            score -= 24

    context_conflicts = {
        "sunrise", "sunset", "night", "orange", "red", "storm", "rain",
        "snow", "fog", "indoor", "portrait", "selfie", "illustration",
    }
    for term in context_conflicts:
        if term in candidate_low and term not in query_low:
            score -= 22

    if total_overlap == 0:
        score -= 80
    elif len(q) >= 3 and total_overlap == 1:
        score -= 20

    score += min(5.0, math.log10(max(1, candidate["width"] * candidate["height"])))
    return score

def choose_visual(query, used_ids):
    candidates = commons_candidates(query)
    ranked = []
    for c in candidates:
        if c["pageid"] in used_ids:
            continue
        c = dict(c)
        c["score"] = visual_score(c, query)
        ranked.append(c)
    ranked.sort(key=lambda x: x["score"], reverse=True)
    if not ranked:
        raise BuildError("visual_not_found", f"No usable Wikimedia image for query: {query}", 422)
    return ranked[0]

def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=40) as r, open(path, "wb") as f:
            shutil.copyfileobj(r, f)
    except Exception as e:
        raise BuildError("visual_download_failed", str(e), 502)

def detect_pause_midpoints(audio_path, sample_rate, channels):
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-f", "s16be", "-ar", str(sample_rate), "-ac", str(channels),
        "-i", str(audio_path),
        "-af", "silencedetect=noise=-25dB:d=0.08",
        "-f", "null", "-"
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        return []

    starts = []
    intervals = []
    for line in p.stderr.splitlines():
        m = re.search(r"silence_start:\s*([0-9.]+)", line)
        if m:
            starts.append(float(m.group(1)))
            continue
        m = re.search(r"silence_end:\s*([0-9.]+)", line)
        if m and starts:
            start = starts.pop(0)
            end = float(m.group(1))
            if end > start:
                intervals.append([start, end])

    merged = []
    for start, end in intervals:
        if merged and start - merged[-1][1] <= 0.08:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    return [
        round((start + end) / 2.0, 4)
        for start, end in merged
        if end - start >= 0.10
    ]

def allocate_timing(scenes, audio_path, sample_rate, channels, audio_duration, target_duration):
    if audio_duration > target_duration + 0.05:
        raise BuildError(
            "voice_too_long",
            f"voice is {audio_duration:.3f}s, target is {target_duration}s; speech will not be cut or sped up",
            422,
        )

    counts = [max(1, len(words(s.get("narration", "")))) for s in scenes]
    total = sum(counts)
    expected = []
    running = 0
    for count in counts[:-1]:
        running += count
        expected.append(audio_duration * running / total)

    pauses = [
        p for p in detect_pause_midpoints(audio_path, sample_rate, channels)
        if 0.30 < p < audio_duration - 0.20
    ]

    boundaries = []
    boundary_sources = []
    previous = 0.0
    for exp in expected:
        candidates = [p for p in pauses if p > previous + 0.25]
        if candidates:
            nearest = min(candidates, key=lambda p: abs(p - exp))
            max_distance = max(1.25, audio_duration * 0.12)
            if abs(nearest - exp) <= max_distance:
                boundary = nearest
                source = "local_silence_alignment"
                pauses.remove(nearest)
            else:
                boundary = exp
                source = "proportional_fallback"
        else:
            boundary = exp
            source = "proportional_fallback"

        boundary = max(previous + 0.25, min(boundary, audio_duration - 0.20))
        boundaries.append(boundary)
        boundary_sources.append(source)
        previous = boundary

    timing = []
    starts = [0.0] + boundaries
    voice_ends = boundaries + [audio_duration]

    for idx, scene in enumerate(scenes):
        start = starts[idx]
        voice_end = voice_ends[idx]
        end = target_duration if idx == len(scenes) - 1 else voice_end
        timing.append({
            "scene": idx + 1,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(end - start, 3),
            "voice_end": round(voice_end, 3),
            "alignment_source": (
                "audio_end"
                if idx == len(scenes) - 1
                else boundary_sources[idx]
            ),
            "narration": scene.get("narration", ""),
            "visual_query": scene.get("visual_query", ""),
        })
    return timing

def render_segment(image_path, duration, out_path):
    filt = (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=20:1[bg2];"
        "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fg2];"
        "[bg2][fg2]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    run([
        "ffmpeg","-y","-loglevel","error",
        "-loop","1","-framerate","30","-i",str(image_path),
        "-t",f"{duration:.3f}",
        "-filter_complex",filt,
        "-map","[v]","-an","-r","30",
        "-c:v","libx264","-preset","veryfast","-crf","21",
        str(out_path),
    ])

def ffprobe(path):
    raw = run([
        "ffprobe","-v","error","-show_streams","-show_entries","format=duration",
        "-of","json",str(path)
    ])
    return json.loads(raw)

def build(payload):
    try:
        job_id = str(uuid.UUID(str(payload.get("job_id"))))
    except Exception:
        raise BuildError("invalid_job_id", "job_id must be UUID")

    target = int(payload.get("target_duration_seconds") or 0)
    if target not in {15,30,45,60}:
        raise BuildError("invalid_duration", "target duration must be 15/30/45/60")

    script_json = payload.get("script_json")
    scenes = script_json.get("scenes") if isinstance(script_json, dict) else None
    if not isinstance(scenes, list) or not scenes:
        raise BuildError("invalid_script", "script_json.scenes is required")

    audio_path = safe_data_path(payload.get("audio_path") or "")
    if not audio_path.is_file():
        raise BuildError("audio_missing", "voice PCM file not found")

    sample_rate = int(payload.get("audio_sample_rate") or 0)
    channels = int(payload.get("audio_channels") or 0)
    if sample_rate <= 0 or channels <= 0:
        raise BuildError("invalid_audio_metadata", "sample rate/channels missing")

    bytes_per_sample = 2
    audio_duration = audio_path.stat().st_size / (sample_rate * channels * bytes_per_sample)
    timing = allocate_timing(
        scenes,
        audio_path,
        sample_rate,
        channels,
        audio_duration,
        float(target),
    )

    job_dir = DATA_DIR / job_id
    assets_dir = job_dir / "assets"
    work_dir = job_dir / "work"
    assets_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    used = set()
    visuals = []
    segment_paths = []

    for idx, (scene, slot) in enumerate(zip(scenes, timing), start=1):
        query = str(scene.get("visual_query") or "").strip()
        if not query:
            raise BuildError("visual_query_missing", f"scene {idx} visual_query missing")
        selected = choose_visual(query, used)
        used.add(selected["pageid"])
        ext = { "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp" }[selected["mime"]]
        image_path = assets_dir / f"scene-{idx:02d}{ext}"
        download(selected["url"], image_path)

        page_url = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(selected["title"].replace(" ", "_"))
        visual = {
            "scene": idx,
            "query": query,
            "title": selected["title"],
            "page_url": page_url,
            "source_url": selected["original_url"],
            "local_path": str(image_path),
            "license": selected["license"],
            "license_url": selected["license_url"],
            "artist": selected["artist"],
            "credit": selected["credit"],
            "width": selected["width"],
            "height": selected["height"],
            "deterministic_score": round(selected["score"], 3),
        }
        visuals.append(visual)

        segment = work_dir / f"segment-{idx:02d}.mp4"
        render_segment(image_path, slot["duration"], segment)
        segment_paths.append(segment)

    concat_file = work_dir / "concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for p in segment_paths:
            escaped = str(p).replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")

    video_no_audio = work_dir / "visuals.mp4"
    run([
        "ffmpeg","-y","-loglevel","error",
        "-f","concat","-safe","0","-i",str(concat_file),
        "-c","copy",str(video_no_audio),
    ])

    padded_audio = work_dir / "voice.m4a"
    pcm_format = "s16be"
    run([
        "ffmpeg","-y","-loglevel","error",
        "-f",pcm_format,"-ar",str(sample_rate),"-ac",str(channels),"-i",str(audio_path),
        "-af","apad","-t",str(target),
        "-c:a","aac","-b:a","160k",str(padded_audio),
    ])

    final_path = DATA_DIR / f"{job_id}-final.mp4"
    run([
        "ffmpeg","-y","-loglevel","error",
        "-i",str(video_no_audio),"-i",str(padded_audio),
        "-map","0:v:0","-map","1:a:0",
        "-c:v","copy","-c:a","copy",
        "-t",str(target),"-movflags","+faststart",
        str(final_path),
    ])

    probe = ffprobe(final_path)
    video_stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "audio"), None)
    duration = float(probe.get("format", {}).get("duration") or 0)
    qa = {
        "duration_seconds": round(duration, 3),
        "width": int((video_stream or {}).get("width") or 0),
        "height": int((video_stream or {}).get("height") or 0),
        "video_codec": (video_stream or {}).get("codec_name"),
        "audio_codec": (audio_stream or {}).get("codec_name"),
        "audio_present": audio_stream is not None,
    }
    qa["pass"] = (
        qa["width"] == 1080
        and qa["height"] == 1920
        and qa["video_codec"] == "h264"
        and qa["audio_codec"] == "aac"
        and qa["audio_present"]
        and abs(duration - target) <= 0.08
    )
    if not qa["pass"]:
        raise BuildError("machine_qa_failed", json.dumps(qa, ensure_ascii=False), 500)

    (job_dir / "visuals.json").write_text(json.dumps(visuals, ensure_ascii=False, indent=2), encoding="utf-8")
    (job_dir / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(work_dir, ignore_errors=True)

    return {
        "job_id": job_id,
        "status": "rendered",
        "video_path": str(final_path),
        "audio_duration_seconds": round(audio_duration, 3),
        "video_duration_seconds": round(duration, 3),
        "visual_assets": visuals,
        "timing": timing,
        "qa": qa,
    }

class Handler(BaseHTTPRequestHandler):
    server_version = "ShortsV2MediaWorker/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_json(self, status, body):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/health":
            return self.send_json(200, {"status": "ok"})
        return self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/build":
            return self.send_json(404, {"error": "not_found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 2_000_000:
                raise BuildError("invalid_body", "request body missing or too large")
            payload = json.loads(self.rfile.read(length))
            result = build(payload)
            return self.send_json(200, result)
        except BuildError as e:
            return self.send_json(e.status, {"error": e.code, "message": str(e)})
        except Exception as e:
            return self.send_json(500, {"error": "internal_error", "message": str(e)})

if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
