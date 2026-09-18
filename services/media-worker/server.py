#!/usr/bin/env python3
import difflib
import html
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import unicodedata
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

WHISPER_CLI = Path(os.environ.get("WHISPER_CLI", "/app/build/bin/whisper-cli"))
WHISPER_MODEL = Path(os.environ.get("WHISPER_MODEL", "/data/models/ggml-base.bin"))
WHISPER_THREADS = max(1, int(os.environ.get("WHISPER_THREADS", "2")))
WHISPER_MODEL_SHA256 = "60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe"
ALIGNMENT_MIN_GLOBAL_COVERAGE = 0.80
ALIGNMENT_MIN_SCENE_COVERAGE = 0.65
ALIGNMENT_MAX_BOUNDARY_SEARCH_CHARS = 80
SUPPORTED_LANGUAGES = {"en", "pl", "ru", "uk"}

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
        "eclipse", "solar eclipse", "lunar eclipse",
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

def search_query_variants(query):
    raw = " ".join(str(query).split())
    tokens = [w for w in words(raw) if w not in STOPWORDS]
    variants = [raw]

    for size in range(len(tokens) - 1, 1, -1):
        variants.append(" ".join(tokens[:size]))

    if len(tokens) >= 2:
        variants.append(" ".join(tokens[:2]))

    seen = set()
    out = []
    for value in variants:
        key = value.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(value.strip())
    return out

def visual_rank(candidate, query):
    query_set = query_tokens(query)
    title_set = query_tokens(candidate.get("title", ""))
    title_overlap = len(query_set & title_set)
    title_precision = title_overlap / max(1, len(title_set))
    unmatched_title_terms = len(title_set - query_set)
    pixels = int(candidate.get("width") or 0) * int(candidate.get("height") or 0)
    pageid = int(candidate.get("pageid") or 0)
    return (
        float(candidate.get("score") or 0),
        title_precision,
        title_overlap,
        -unmatched_title_terms,
        pixels,
        -pageid,
    )

def choose_visual(query, used_ids):
    attempted = []
    candidates_by_page = {}

    for search_query in search_query_variants(query):
        attempted.append(search_query)
        for raw_candidate in commons_candidates(search_query):
            pageid = raw_candidate["pageid"]
            if pageid in used_ids or pageid in candidates_by_page:
                continue
            candidate = dict(raw_candidate)
            candidate["score"] = visual_score(candidate, query)
            candidate["resolved_query"] = search_query
            candidates_by_page[pageid] = candidate

    if candidates_by_page:
        return max(
            candidates_by_page.values(),
            key=lambda candidate: visual_rank(candidate, query),
        )

    raise BuildError(
        "visual_not_found",
        "No usable Wikimedia image after query fallback: " + " -> ".join(attempted),
        422,
    )

def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=40) as r, open(path, "wb") as f:
            shutil.copyfileobj(r, f)
    except Exception as e:
        raise BuildError("visual_download_failed", str(e), 502)

def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def ensure_aligner_ready():
    if not WHISPER_CLI.is_file() or not os.access(WHISPER_CLI, os.X_OK):
        raise BuildError("alignment_runtime_missing", f"whisper-cli not executable: {WHISPER_CLI}", 500)
    if not WHISPER_MODEL.is_file():
        raise BuildError("alignment_model_missing", f"Whisper model missing: {WHISPER_MODEL}", 500)
    actual = file_sha256(WHISPER_MODEL)
    if actual != WHISPER_MODEL_SHA256:
        raise BuildError(
            "alignment_model_invalid",
            f"Whisper model sha256 mismatch: expected {WHISPER_MODEL_SHA256}, got {actual}",
            500,
        )

def alignment_text(value):
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(ch for ch in normalized if ch.isalnum())

def whisper_alignment(script_text, audio_path, sample_rate, channels, language, work_dir):
    ensure_aligner_ready()

    wav_path = work_dir / "alignment.wav"
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "s16le", "-ar", str(sample_rate), "-ac", str(channels),
        "-i", str(audio_path),
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        str(wav_path),
    ])

    output_prefix = work_dir / "alignment"
    run([
        str(WHISPER_CLI),
        "-m", str(WHISPER_MODEL),
        "-f", str(wav_path),
        "-l", language,
        "-t", str(WHISPER_THREADS),
        "-p", "1",
        "-ng",
        "-dtw", "base",
        "-ojf",
        "--prompt", script_text,
        "-of", str(output_prefix),
    ])

    json_path = Path(str(output_prefix) + ".json")
    if not json_path.is_file():
        raise BuildError("alignment_failed", "whisper-cli produced no JSON output", 500)
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise BuildError("alignment_failed", f"invalid Whisper JSON: {e}", 500)

def allocate_timing(script_json, audio_path, sample_rate, channels, audio_duration, target_duration, language, work_dir):
    if audio_duration > target_duration + 0.05:
        raise BuildError(
            "voice_too_long",
            f"voice is {audio_duration:.3f}s, target is {target_duration}s; speech will not be cut or sped up",
            422,
        )

    if language not in SUPPORTED_LANGUAGES:
        raise BuildError("invalid_language", "language must be en/pl/ru/uk")

    scenes = script_json.get("scenes") if isinstance(script_json, dict) else None
    if not isinstance(scenes, list) or not scenes:
        raise BuildError("invalid_script", "script_json.scenes is required")

    scene_norms = [alignment_text(scene.get("narration", "")) for scene in scenes]
    if any(not value for value in scene_norms):
        raise BuildError("alignment_failed", "scene narration normalizes to empty text", 422)

    joined_script = " ".join(str(scene.get("narration", "")).strip() for scene in scenes)
    script_text = str(script_json.get("script") or joined_script).strip()
    script_norm = alignment_text(script_text)
    joined_norm = "".join(scene_norms)
    if script_norm != joined_norm:
        raise BuildError("alignment_failed", "script text does not match scene narration sequence", 422)

    result = whisper_alignment(
        script_text,
        audio_path,
        sample_rate,
        channels,
        language,
        work_dir,
    )

    tokens = []
    for segment in result.get("transcription", []):
        for token in segment.get("tokens", []):
            token_text = str(token.get("text") or "")
            token_norm = alignment_text(token_text)
            offsets = token.get("offsets") or {}
            start_ms = offsets.get("from")
            end_ms = offsets.get("to")
            if not token_norm or token_text.startswith("[_"):
                continue
            if not isinstance(start_ms, (int, float)) or not isinstance(end_ms, (int, float)):
                continue
            if end_ms < start_ms:
                continue
            tokens.append({
                "text": token_text,
                "norm": token_norm,
                "start_ms": float(start_ms),
                "end_ms": float(end_ms),
            })

    if not tokens:
        raise BuildError("alignment_failed", "Whisper returned no timed speech tokens", 422)

    asr_norm = "".join(token["norm"] for token in tokens)
    asr_char_token = []
    for token_index, token in enumerate(tokens):
        asr_char_token.extend([token_index] * len(token["norm"]))

    matcher = difflib.SequenceMatcher(a=script_norm, b=asr_norm, autojunk=False)
    script_to_asr = {}
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            script_to_asr[block.a + offset] = block.b + offset

    global_coverage = len(script_to_asr) / max(1, len(script_norm))
    if global_coverage < ALIGNMENT_MIN_GLOBAL_COVERAGE:
        raise BuildError(
            "alignment_failed",
            f"global transcript coverage {global_coverage:.3f} below {ALIGNMENT_MIN_GLOBAL_COVERAGE:.3f}",
            422,
        )

    scene_spans = []
    scene_coverages = []
    cursor = 0
    for scene_norm in scene_norms:
        start = cursor
        end = cursor + len(scene_norm)
        coverage = sum(i in script_to_asr for i in range(start, end)) / max(1, end - start)
        if coverage < ALIGNMENT_MIN_SCENE_COVERAGE:
            raise BuildError(
                "alignment_failed",
                f"scene transcript coverage {coverage:.3f} below {ALIGNMENT_MIN_SCENE_COVERAGE:.3f}",
                422,
            )
        scene_spans.append((start, end))
        scene_coverages.append(coverage)
        cursor = end

    boundaries = []
    previous = 0.0
    for _, boundary_char in scene_spans[:-1]:
        left = next(
            (
                idx
                for idx in range(
                    boundary_char - 1,
                    max(-1, boundary_char - ALIGNMENT_MAX_BOUNDARY_SEARCH_CHARS - 1),
                    -1,
                )
                if idx in script_to_asr
            ),
            None,
        )
        right = next(
            (
                idx
                for idx in range(
                    boundary_char,
                    min(len(script_norm), boundary_char + ALIGNMENT_MAX_BOUNDARY_SEARCH_CHARS),
                )
                if idx in script_to_asr
            ),
            None,
        )
        if left is None or right is None:
            raise BuildError("alignment_failed", "unable to map a scene boundary to speech tokens", 422)

        left_token = tokens[asr_char_token[script_to_asr[left]]]
        right_token = tokens[asr_char_token[script_to_asr[right]]]
        left_end = left_token["end_ms"] / 1000.0
        right_start = right_token["start_ms"] / 1000.0
        if right_start < left_end - 0.25:
            raise BuildError("alignment_failed", "overlapping token timestamps at scene boundary", 422)

        boundary = (left_end + right_start) / 2.0
        if boundary <= previous + 0.10 or boundary >= audio_duration - 0.10:
            raise BuildError("alignment_failed", "non-monotonic or out-of-range scene boundary", 422)
        boundaries.append(boundary)
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
            "alignment_source": "audio_end" if idx == len(scenes) - 1 else "local_whisper_token_alignment",
            "alignment_coverage": round(scene_coverages[idx], 4),
            "narration": scene.get("narration", ""),
            "visual_query": scene.get("visual_query", ""),
        })

    transcript = " ".join(
        str(segment.get("text") or "").strip()
        for segment in result.get("transcription", [])
        if str(segment.get("text") or "").strip()
    )
    alignment = {
        "engine": "whisper.cpp",
        "model": "ggml-base",
        "language": language,
        "global_coverage": round(global_coverage, 4),
        "scene_coverages": [round(value, 4) for value in scene_coverages],
        "boundaries_seconds": [round(value, 3) for value in boundaries],
        "timed_token_count": len(tokens),
        "transcript": transcript,
        "fallback_used": False,
    }
    return timing, alignment

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

    language = str(payload.get("language") or "").strip()
    if language not in SUPPORTED_LANGUAGES:
        raise BuildError("invalid_language", "language must be en/pl/ru/uk")

    audio_path = safe_data_path(payload.get("audio_path") or "")
    if not audio_path.is_file():
        raise BuildError("audio_missing", "voice PCM file not found")

    sample_rate = int(payload.get("audio_sample_rate") or 0)
    channels = int(payload.get("audio_channels") or 0)
    if sample_rate <= 0 or channels <= 0:
        raise BuildError("invalid_audio_metadata", "sample rate/channels missing")

    bytes_per_sample = 2
    audio_duration = audio_path.stat().st_size / (sample_rate * channels * bytes_per_sample)

    job_dir = DATA_DIR / job_id
    assets_dir = job_dir / "assets"
    work_dir = job_dir / "work"
    assets_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    timing, alignment = allocate_timing(
        script_json,
        audio_path,
        sample_rate,
        channels,
        audio_duration,
        float(target),
        language,
        work_dir,
    )

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
            "resolved_query": selected.get("resolved_query", query),
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
    pcm_format = "s16le"
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
        "alignment": alignment,
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
