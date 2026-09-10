import {execFileSync} from "node:child_process";
import {createHash, randomBytes} from "node:crypto";
import {createReadStream} from "node:fs";
import {readFile, rm, stat} from "node:fs/promises";
import {dirname, extname, resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {bundle} from "@remotion/bundler";
import {renderMedia, selectComposition} from "@remotion/renderer";
import sharp from "sharp";
import {clusterAverageHashes, hammingDistance} from "./visual-quality.mjs";
import {parseSingleByteRange} from "./media-range.mjs";
import {compileDiagramSpec} from "./diagram-compiler.mjs";

const browserExecutable = "/usr/bin/chromium";
const entryPoint = resolve(dirname(fileURLToPath(import.meta.url)), "../remotion/index.tsx");
const activeAssets = new Map();
let bundlePromise = null;

const mimeForPath = (path) => ({
  ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif", ".svg": "image/svg+xml",
  ".mp4": "video/mp4", ".wav": "audio/wav", ".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".aac": "audio/aac",
}[extname(path).toLowerCase()] ?? "application/octet-stream");

const getServeUrl = () => {
  if (!bundlePromise) {
    bundlePromise = bundle({entryPoint, publicDir: null, rootDir: resolve(dirname(entryPoint), "..")});
  }
  return bundlePromise;
};

function normalizeWordTiming(wordTiming, durationSeconds) {
  if (!wordTiming || wordTiming.version !== "provider-word-timing-v1" || !Array.isArray(wordTiming.words) || wordTiming.words.length === 0) {
    throw new Error("V6 renderer requires provider-word-timing-v1");
  }
  const words = wordTiming.words.map((word, index) => {
    const text = String(word?.text ?? "").replace(/\s+/gu, " ").trim();
    const start = Number(word?.start_seconds), end = Number(word?.end_seconds);
    if (!text || !Number.isFinite(start) || !Number.isFinite(end) || start < 0 || end <= start || end > durationSeconds + 0.01) {
      throw new Error(`V6 renderer word timing ${index + 1} is invalid`);
    }
    if (index > 0 && start < Number(wordTiming.words[index - 1]?.end_seconds) - 0.002) throw new Error(`V6 renderer word timing ${index + 1} overlaps`);
    return {text, start_seconds: start, end_seconds: end};
  });
  return words;
}

async function analyzeFrame(buffer) {
  const image = sharp(buffer).removeAlpha();
  const meta = await image.metadata();
  if (!meta.width || !meta.height) throw new Error("rendered frame has no dimensions");
  const visualHeight = Math.max(1, Math.floor(meta.height * 0.72));
  const {data} = await image.extract({left: 0, top: 0, width: meta.width, height: visualHeight})
    .resize(16, 16, {fit: "fill"}).grayscale().raw().toBuffer({resolveWithObject: true});
  const values = [...data];
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((sum, value) => sum + ((value - mean) ** 2), 0) / values.length;
  const stddev = Math.sqrt(variance);
  const brightRatio = values.filter((value) => value >= 32).length / values.length;
  const bits = values.map((value) => value >= mean ? 1 : 0);
  return {mean, stddev, brightRatio, bits};
}

function extractFrame(videoPath, timeSeconds) {
  const time = Math.max(0, Number(timeSeconds));
  return execFileSync("ffmpeg", ["-v", "error", "-ss", time.toFixed(6), "-i", videoPath, "-frames:v", "1", "-vf", "scale=270:480:flags=lanczos", "-f", "image2pipe", "-vcodec", "png", "pipe:1"], {
    stdio: ["ignore", "pipe", "pipe"], maxBuffer: 32 * 1024 * 1024,
  });
}

export async function inspectV6RenderedPixels(videoPath, shots) {
  if (!Array.isArray(shots) || shots.length === 0) throw new Error("V6 pixel QA requires shots");
  const samples = [];
  for (const shot of shots) {
    const start = Number(shot.start_seconds), end = Number(shot.end_seconds);
    if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) throw new Error(`V6 pixel QA shot ${shot.shot_number} timing is invalid`);
    const time = start + ((end - start) * 0.5);
    const metrics = await analyzeFrame(extractFrame(videoPath, time));
    samples.push({shot_number: Number(shot.shot_number), time_seconds: Number(time.toFixed(4)), ...metrics});
  }
  const black = samples.filter((sample) => sample.mean < 10 && sample.brightRatio < 0.025);
  const flat = samples.filter((sample) => sample.stddev < 2.0);
  let adjacentDuplicates = 0;
  for (let i = 1; i < samples.length; i += 1) if (hammingDistance(samples[i - 1].bits, samples[i].bits) <= 18) adjacentDuplicates += 1;
  const clusters = clusterAverageHashes(samples.map((sample) => sample.bits), 18);
  const pass = black.length === 0 && flat.length === 0 && adjacentDuplicates === 0 && clusters.length === samples.length;
  return {
    version: "remotion-pixel-qa-v1",
    sample_count: samples.length,
    required_sample_count: shots.length,
    rendered_visual_state_count: clusters.length,
    required_rendered_visual_state_count: shots.length,
    rendered_adjacent_visual_state_duplicate_count: adjacentDuplicates,
    black_frame_sample_count: black.length,
    flat_frame_sample_count: flat.length,
    samples: samples.map(({bits, ...sample}) => ({...sample, mean_luma: Number(sample.mean.toFixed(3)), luma_stddev: Number(sample.stddev.toFixed(3)), bright_ratio: Number(sample.brightRatio.toFixed(4))})),
    pass,
  };
}

export async function serveV6RenderAsset(request, response, pathname) {
  const match = /^\/internal\/render-v6\/([a-f0-9]{32})\/([a-z0-9-]+)$/u.exec(pathname);
  if (!match) return false;
  const bucket = activeAssets.get(match[1]);
  const asset = bucket?.get(match[2]);
  if (!asset || !["GET", "HEAD"].includes(request.method ?? "")) {
    response.writeHead(404, {"Cache-Control": "no-store"}); response.end(); return true;
  }
  const info = await stat(asset.path);
  const rangeHeader = request.headers.range;
  let range = null;
  try { range = parseSingleByteRange(rangeHeader, info.size); } catch {
    response.writeHead(416, {"Content-Range": `bytes */${info.size}`, "Cache-Control": "no-store"}); response.end(); return true;
  }
  const headers = {"Content-Type": asset.mime, "Accept-Ranges": "bytes", "Cache-Control": "no-store", "Access-Control-Allow-Origin": "*"};
  if (range) {
    response.writeHead(206, {...headers, "Content-Length": String(range.length), "Content-Range": `bytes ${range.start}-${range.end}/${info.size}`});
    if (request.method === "HEAD") { response.end(); return true; }
    createReadStream(asset.path, {start: range.start, end: range.end}).pipe(response); return true;
  }
  response.writeHead(200, {...headers, "Content-Length": String(info.size)});
  if (request.method === "HEAD") { response.end(); return true; }
  createReadStream(asset.path).pipe(response); return true;
}

export async function renderV6Composition({jobId, audioAbsolutePath, outputPath, durationSeconds, shots, wordTiming, workerPort}) {
  if (!Array.isArray(shots) || shots.length === 0) throw new Error("V6 renderer requires shots");
  const words = normalizeWordTiming(wordTiming, durationSeconds);
  const token = randomBytes(16).toString("hex");
  const bucket = new Map();
  bucket.set("audio", {path: audioAbsolutePath, mime: mimeForPath(audioAbsolutePath)});
  const visualTrack = shots.map((shot, index) => {
    const id = `shot-${index + 1}`;
    const representation = String(shot.representation || (shot.visual_kind === "factual_graphic" ? "factual_graphic" : "exact_media"));
    const base = {
      shot_number: Number(shot.shot_number), start_seconds: Number(shot.start_seconds), end_seconds: Number(shot.end_seconds),
      representation,
      visual_form: String(shot.visual_form || (shot.visual_kind === "factual_graphic" ? "diagram" : "photo")),
      crop_safe_portrait: shot.crop_safe_portrait === true,
    };
    if (representation === "diagram") {
      const shotId = String(shot.shot_id || `shot-${Number(shot.shot_number)}`);
      const graphic = compileDiagramSpec(shot.diagram_spec, Number(shot.duration_seconds), {expectedShotId: shotId, allowedFactIds: shot.grounded_fact_ids});
      return {...base, media_type: "image", graphic};
    }
    if (!shot.visual_path?.absolutePath) throw new Error(`V6 media shot ${shot.shot_number} has no resolved visual path`);
    bucket.set(id, {path: shot.visual_path.absolutePath, mime: mimeForPath(shot.visual_path.absolutePath)});
    return {...base, src: `http://127.0.0.1:${workerPort}/internal/render-v6/${token}/${id}`, media_type: shot.visual_media_type === "video" ? "video" : "image"};
  });
  activeAssets.set(token, bucket);
  try {
    const serveUrl = await getServeUrl();
    const inputProps = {
      duration_seconds: Number(durationSeconds),
      audio_src: `http://127.0.0.1:${workerPort}/internal/render-v6/${token}/audio`,
      captions: words,
      visual_track: visualTrack,
    };
    const common = {serveUrl, inputProps, browserExecutable, chromeMode: "chrome-for-testing", logLevel: "error"};
    const composition = await selectComposition({...common, id: "V6VerticalShort"});
    const remotionOutputPath = `${outputPath}.remotion-${randomBytes(8).toString("hex")}.mp4`;
    try {
      await renderMedia({
        ...common, composition, codec: "h264", audioCodec: "aac", pixelFormat: "yuv420p", crf: 20,
        outputLocation: remotionOutputPath, overwrite: true, concurrency: 1, audioBitrate: "192k", sampleRate: 48000,
        licenseKey: "free-license",
      });
      execFileSync("ffmpeg", [
        "-v", "error", "-y", "-i", remotionOutputPath,
        "-vf", "scale=in_range=full:out_range=tv,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.1",
        "-pix_fmt", "yuv420p", "-color_range", "tv",
        "-c:a", "copy", "-movflags", "+faststart", outputPath,
      ], {stdio: ["ignore", "pipe", "pipe"], maxBuffer: 64 * 1024 * 1024});
      const qa = await inspectV6RenderedPixels(outputPath, shots);
      if (!qa.pass) throw new Error(`V6 rendered pixel QA failed: states=${qa.rendered_visual_state_count}/${qa.required_rendered_visual_state_count}, adjacent=${qa.rendered_adjacent_visual_state_duplicate_count}, black=${qa.black_frame_sample_count}, flat=${qa.flat_frame_sample_count}`);
      const bytes = await readFile(outputPath);
      return {artifact_sha256: createHash("sha256").update(bytes).digest("hex"), bytes: bytes.length, pixel_qa: qa};
    } finally {
      await rm(remotionOutputPath, {force: true}).catch(() => {});
    }
  } finally {
    activeAssets.delete(token);
  }
}
