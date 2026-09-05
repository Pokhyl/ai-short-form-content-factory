import { execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { createReadStream } from "node:fs";
import { mkdir, rename, rm, stat, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import sharp from "sharp";
import edgeTtsPackage from "node-edge-tts";
import { pipeline, env, RawImage } from "@huggingface/transformers";
import { dirname, extname, resolve, sep } from "node:path";
import { edgeProviderBudgetMilliseconds } from "./edge-provider-budget.mjs";
import { parseSingleByteRange } from "./media-range.mjs";
import { buildVisualBeatFilters } from "./visual-framing.mjs";
import { discoverVisualCandidates } from "./visual-discovery.mjs";
import { buildVisualDiscoveryOptions } from "./visual-discovery-request.mjs";
import { clusterAverageHashes, evaluateVisualSequence, evaluateVisualShotSequence, requiredRenderedShotStateCount } from "./visual-quality.mjs";

const { EdgeTTS } = edgeTtsPackage;

const port = Number(process.env.PORT ?? 3001);
const dataRoot = resolve(process.env.MEDIA_DATA_ROOT ?? "/data");
const maxJsonBodyBytes = 8 * 1024 * 1024;
const maxVisualBodyBytes = 50 * 1024 * 1024;
const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const base64Pattern = /^[A-Za-z0-9+/]+={0,2}$/;
const supportedImageTypes = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
  "image/svg+xml",
]);
const supportedVideoTypes = new Set(["video/mp4"]);
const freeFallbackVoices = Object.freeze({
  en: { voice: "en-US-AndrewNeural", locale: "en-US" },
  pl: { voice: "pl-PL-MarekNeural", locale: "pl-PL" },
  ru: { voice: "ru-RU-DmitryNeural", locale: "ru-RU" },
  uk: { voice: "uk-UA-OstapNeural", locale: "uk-UA" },
});
const fallbackFontPath =
  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf";
const siglipModel =
  process.env.SIGLIP_MODEL ?? "Xenova/siglip-base-patch16-224";
const siglipDtype = process.env.SIGLIP_DTYPE ?? "q4";
const siglipCacheDir = resolve(
  process.env.TRANSFORMERS_CACHE ?? `${dataRoot}/models/huggingface`,
);
const maxRankCandidates = 10;
const maxRankPreviewsPerCandidate = 3;
const maxRankPreviewImages = maxRankCandidates * maxRankPreviewsPerCandidate;
const trustedPreviewHosts = new Set([
  "cdn.pixabay.com",
  "pixabay.com",
  "images.pexels.com",
  "upload.wikimedia.org",
  "thumb.wikimedia.org",
]);

env.cacheDir = siglipCacheDir;
env.allowRemoteModels = true;

let siglipPipelinePromise = null;
const maxConcurrentPreviewFetches = 3;
const previewFetchTimeoutMs = 10000;
const previewCacheMaxEntries = 48;
const previewCacheMaxBytes = 32 * 1024 * 1024;
let previewCacheBytes = 0;
const previewBufferCache = new Map();
const previewFetchInflight = new Map();
let availablePreviewFetchSlots = maxConcurrentPreviewFetches;
let wikimediaPreviewFetchTail = Promise.resolve();
const previewFetchWaiters = [];
let siglipInferenceTail = Promise.resolve();
const previewUserAgent =
  "ai-short-form-content-factory/1.0 (https://github.com/Pokhyl/ai-short-form-content-factory)";

function sleep(milliseconds) {
  return new Promise((resolvePromise) => setTimeout(resolvePromise, milliseconds));
}

async function acquirePreviewFetchSlot() {
  if (availablePreviewFetchSlots > 0) {
    availablePreviewFetchSlots -= 1;
    return;
  }

  await new Promise((resolvePromise) => previewFetchWaiters.push(resolvePromise));
}

function releasePreviewFetchSlot() {
  const nextWaiter = previewFetchWaiters.shift();
  if (nextWaiter) {
    nextWaiter();
    return;
  }

  availablePreviewFetchSlots += 1;
}

async function withPreviewFetchSlot(operation) {
  await acquirePreviewFetchSlot();
  try {
    return await operation();
  } finally {
    releasePreviewFetchSlot();
  }
}

async function fetchPreviewAttempt(url) {
  const executeFetch = () => withPreviewFetchSlot(async () => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), previewFetchTimeoutMs);

    try {
      const response = await fetch(url, {
        headers: { "User-Agent": previewUserAgent },
        signal: controller.signal,
      });
      const retryAfterSeconds = Number(response.headers.get("retry-after"));

      if (!response.ok) {
        return {
          ok: false,
          status: response.status,
          retryAfterSeconds: Number.isFinite(retryAfterSeconds) ? retryAfterSeconds : null,
          buffer: null,
        };
      }

      const buffer = Buffer.from(await response.arrayBuffer());
      return {
        ok: true,
        status: response.status,
        retryAfterSeconds: null,
        buffer,
      };
    } finally {
      clearTimeout(timeout);
    }
  });

  let hostname = "";
  try {
    hostname = new URL(url).hostname.toLowerCase();
  } catch {
    hostname = "";
  }

  if (hostname === "upload.wikimedia.org") {
    const run = async () => {
      const result = await executeFetch();
      await sleep(180);
      return result;
    };
    const queued = wikimediaPreviewFetchTail.then(run, run);
    wikimediaPreviewFetchTail = queued.then(() => undefined, () => undefined);
    return queued;
  }

  return executeFetch();
}

function readCachedPreview(url) {
  const cached = previewBufferCache.get(url);
  if (!cached) return null;
  previewBufferCache.delete(url);
  previewBufferCache.set(url, cached);
  return cached;
}

function rememberPreview(url, buffer) {
  if (!Buffer.isBuffer(buffer) || buffer.length <= 0 || buffer.length > previewCacheMaxBytes) return;
  const previous = previewBufferCache.get(url);
  if (previous) previewCacheBytes -= previous.length;
  previewBufferCache.delete(url);
  previewBufferCache.set(url, buffer);
  previewCacheBytes += buffer.length;
  while (previewBufferCache.size > previewCacheMaxEntries || previewCacheBytes > previewCacheMaxBytes) {
    const oldestKey = previewBufferCache.keys().next().value;
    if (oldestKey === undefined) break;
    const oldest = previewBufferCache.get(oldestKey);
    previewBufferCache.delete(oldestKey);
    previewCacheBytes -= oldest?.length ?? 0;
  }
}

async function fetchPreviewCached(url) {
  const cached = readCachedPreview(url);
  if (cached) return { ok: true, status: 200, retryAfterSeconds: null, buffer: cached, cache_hit: true };
  const inflight = previewFetchInflight.get(url);
  if (inflight) return inflight;
  const operation = (async () => {
    const result = await fetchPreviewAttempt(url);
    if (result.ok && result.buffer) rememberPreview(url, result.buffer);
    return { ...result, cache_hit: false };
  })();
  previewFetchInflight.set(url, operation);
  try {
    return await operation;
  } finally {
    if (previewFetchInflight.get(url) === operation) previewFetchInflight.delete(url);
  }
}

async function inlineVisualReviewImages(request, response) {
  const body = await readJsonBody(request);
  const input = Array.isArray(body.input) ? body.input : [];
  if (!input.length || input.length > 80) {
    throw new HttpError(400, "invalid_visual_review_input", "Visual review input must contain 1-80 items");
  }

  const output = [];
  let imageCount = 0;
  for (const item of input) {
    if (item?.type !== "image") {
      output.push(item);
      continue;
    }
    const rawUrl = String(item.uri ?? "").trim();
    let parsedUrl;
    try {
      parsedUrl = new URL(rawUrl);
    } catch {
      throw new HttpError(400, "invalid_visual_review_url", "Visual review image URL is invalid");
    }
    if (parsedUrl.protocol !== "https:" || !trustedPreviewHosts.has(parsedUrl.hostname)) {
      throw new HttpError(400, "untrusted_visual_review_url", `Untrusted visual review host: ${parsedUrl.hostname}`);
    }
    const fetched = await fetchPreviewCached(rawUrl);
    if (!fetched.ok || !fetched.buffer) {
      throw new HttpError(502, "visual_review_fetch_failed", `Could not fetch visual review image: ${fetched.status}`);
    }
    const normalized = await sharp(fetched.buffer)
      .rotate()
      .resize({ width: 448, height: 448, fit: "inside", withoutEnlargement: true })
      .jpeg({ quality: 72, progressive: true })
      .toBuffer();
    output.push({ type: "image", data: normalized.toString("base64"), mime_type: "image/jpeg" });
    imageCount += 1;
  }
  if (!imageCount) {
    throw new HttpError(400, "visual_review_images_missing", "Visual review input contains no images");
  }
  sendJson(response, 200, { input: output, image_count: imageCount });
}

async function runSiglipInference(classifier, previewImages, query) {
  const run = () => classifier(
    previewImages,
    [query],
    { hypothesis_template: "{}" },
  );
  const queued = siglipInferenceTail.then(run, run);
  siglipInferenceTail = queued.then(() => undefined, () => undefined);
  return queued;
}

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error("PORT must be a valid TCP port");
}

class HttpError extends Error {
  constructor(statusCode, code, message) {
    super(message);
    this.name = "HttpError";
    this.statusCode = statusCode;
    this.code = code;
  }
}

function readToolVersion(binary) {
  const output = execFileSync(binary, ["-version"], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });

  return output.split("\n")[0].trim();
}

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "Content-Type": "application/json",
    "Cache-Control": "no-store",
  });
  response.end(JSON.stringify(payload));
}

async function readBody(request, maxBytes) {
  const chunks = [];
  let totalBytes = 0;

  for await (const chunk of request) {
    totalBytes += chunk.length;

    if (totalBytes > maxBytes) {
      throw new HttpError(
        413,
        "payload_too_large",
        `Request body exceeds ${maxBytes} bytes`,
      );
    }

    chunks.push(chunk);
  }

  if (totalBytes === 0) {
    throw new HttpError(400, "empty_body", "Request body is required");
  }

  return Buffer.concat(chunks);
}

async function readJsonBody(request) {
  const body = await readBody(request, maxJsonBodyBytes);
  let parsed;

  try {
    parsed = JSON.parse(body.toString("utf8"));
  } catch {
    throw new HttpError(400, "invalid_json", "Request body must be valid JSON");
  }

  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new HttpError(400, "invalid_json_object", "JSON body must be an object");
  }

  return parsed;
}

function decodeAudioBase64(value) {
  if (typeof value !== "string" || value.length === 0) {
    throw new HttpError(
      400,
      "invalid_audio_base64",
      "audio_base64 must be a non-empty base64 string",
    );
  }

  if (!base64Pattern.test(value) || value.length % 4 !== 0) {
    throw new HttpError(
      400,
      "invalid_audio_base64",
      "audio_base64 is not canonical base64",
    );
  }

  const audio = Buffer.from(value, "base64");

  if (
    audio.length === 0 ||
    audio.toString("base64").replace(/=+$/u, "") !==
      value.replace(/=+$/u, "")
  ) {
    throw new HttpError(
      400,
      "invalid_audio_base64",
      "audio_base64 could not be decoded safely",
    );
  }

  return audio;
}

function validatePreviewUrl(value) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new HttpError(
      400,
      "invalid_preview_url",
      "preview_url must be a non-empty HTTPS URL",
    );
  }

  let parsed;

  try {
    parsed = new URL(value);
  } catch {
    throw new HttpError(400, "invalid_preview_url", "preview_url is invalid");
  }

  if (
    parsed.protocol !== "https:" ||
    !trustedPreviewHosts.has(parsed.hostname.toLowerCase())
  ) {
    throw new HttpError(
      400,
      "untrusted_preview_url",
      `preview_url host is not allowed: ${parsed.hostname}`,
    );
  }

  return parsed.toString();
}

function getSiglipPipeline() {
  if (siglipPipelinePromise === null) {
    siglipPipelinePromise = pipeline(
      "zero-shot-image-classification",
      siglipModel,
      { dtype: siglipDtype },
    ).catch((error) => {
      siglipPipelinePromise = null;
      throw error;
    });
  }

  return siglipPipelinePromise;
}

function validateJobAndScene(jobId, sceneNumber) {
  if (!uuidPattern.test(jobId)) {
    throw new HttpError(400, "invalid_job_id", "job_id must be a valid UUID");
  }

  if (!Number.isInteger(sceneNumber) || sceneNumber < 1 || sceneNumber > 1000) {
    throw new HttpError(
      400,
      "invalid_scene_number",
      "scene_number must be an integer between 1 and 1000",
    );
  }
}

function buildAudioPath(jobId, sceneNumber) {
  validateJobAndScene(jobId, sceneNumber);

  const fileName = `scene-${String(sceneNumber).padStart(2, "0")}.mp3`;
  const relativePath = `jobs/${jobId.toLowerCase()}/voiceover/${fileName}`;
  const absolutePath = resolve(dataRoot, relativePath);

  if (
    absolutePath !== dataRoot &&
    !absolutePath.startsWith(`${dataRoot}${sep}`)
  ) {
    throw new HttpError(400, "invalid_audio_path", "Resolved audio path is unsafe");
  }

  return { relativePath, absolutePath };
}

function buildVisualPath(jobId, slotNumber, extension = "jpg", prefix = "scene") {
  validateJobAndScene(jobId, slotNumber);

  if (!new Set(["jpg", "mp4"]).has(extension)) {
    throw new HttpError(400, "invalid_visual_extension", "Visual extension is invalid");
  }
  if (!new Set(["scene", "shot"]).has(prefix)) {
    throw new HttpError(400, "invalid_visual_slot", "Visual slot prefix is invalid");
  }

  const fileName = `${prefix}-${String(slotNumber).padStart(2, "0")}.${extension}`;
  const relativePath = `jobs/${jobId.toLowerCase()}/visuals/${fileName}`;
  const absolutePath = resolve(dataRoot, relativePath);

  if (
    absolutePath !== dataRoot &&
    !absolutePath.startsWith(`${dataRoot}${sep}`)
  ) {
    throw new HttpError(400, "invalid_visual_path", "Resolved visual path is unsafe");
  }

  return { relativePath, absolutePath };
}

function buildContinuousVoiceoverPath(jobId) {
  if (!uuidPattern.test(jobId)) {
    throw new HttpError(400, "invalid_job_id", "job_id must be a valid UUID");
  }
  const relativePath = `jobs/${jobId.toLowerCase()}/voiceover/full.wav`;
  const absolutePath = resolve(dataRoot, relativePath);
  if (absolutePath === dataRoot || !absolutePath.startsWith(`${dataRoot}${sep}`)) {
    throw new HttpError(400, "invalid_audio_path", "Resolved voiceover path is unsafe");
  }
  return { relativePath, absolutePath };
}

function probeDurationSeconds(filePath) {
  const output = execFileSync(
    "ffprobe",
    [
      "-v",
      "error",
      "-show_entries",
      "format=duration",
      "-of",
      "default=noprint_wrappers=1:nokey=1",
      filePath,
    ],
    {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
    },
  ).trim();

  const durationSeconds = Number(output);

  if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) {
    throw new Error(`ffprobe returned invalid duration: ${output}`);
  }

  return durationSeconds;
}

function probeImage(filePath) {
  const output = execFileSync(
    "ffprobe",
    [
      "-v",
      "error",
      "-select_streams",
      "v:0",
      "-show_entries",
      "stream=codec_name,width,height,pix_fmt",
      "-of",
      "json",
      filePath,
    ],
    {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
    },
  );

  const parsed = JSON.parse(output);
  const stream = parsed.streams?.[0];
  const width = Number(stream?.width);
  const height = Number(stream?.height);

  if (!stream || !Number.isInteger(width) || width <= 0 || !Number.isInteger(height) || height <= 0) {
    throw new Error("ffprobe did not return a valid image stream");
  }

  return {
    codec_name: stream.codec_name ?? null,
    width,
    height,
    pix_fmt: stream.pix_fmt ?? null,
  };
}

function probeVideoSource(filePath) {
  const output = execFileSync(
    "ffprobe",
    [
      "-v", "error",
      "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,pix_fmt",
      "-of", "json",
      filePath,
    ],
    { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
  );
  const parsed = JSON.parse(output);
  const video = parsed.streams?.find((stream) => stream.codec_type === "video");
  const duration = Number(parsed.format?.duration);
  const width = Number(video?.width);
  const height = Number(video?.height);
  if (!video || !Number.isInteger(width) || width <= 0 || !Number.isInteger(height) || height <= 0 || !Number.isFinite(duration) || duration <= 0) {
    throw new Error("ffprobe did not return a valid video stream");
  }
  return { codec_name: video.codec_name ?? null, width, height, pix_fmt: video.pix_fmt ?? null, duration_seconds: duration };
}

function probeAnimatedImage(filePath) {
  const output = execFileSync(
    "ffprobe",
    [
      "-v", "error",
      "-count_frames",
      "-select_streams", "v:0",
      "-show_entries", "format=duration:stream=codec_name,width,height,pix_fmt,nb_frames,nb_read_frames",
      "-of", "json",
      filePath,
    ],
    { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
  );
  const parsed = JSON.parse(output);
  const video = parsed.streams?.[0];
  const width = Number(video?.width);
  const height = Number(video?.height);
  const frameCount = Number(video?.nb_read_frames ?? video?.nb_frames);
  const duration = Number(parsed.format?.duration);
  if (!video || !Number.isInteger(width) || width <= 0 || !Number.isInteger(height) || height <= 0) {
    throw new Error("ffprobe did not return a valid GIF stream");
  }
  return {
    codec_name: video.codec_name ?? null,
    width,
    height,
    pix_fmt: video.pix_fmt ?? null,
    frame_count: Number.isFinite(frameCount) ? frameCount : 1,
    duration_seconds: Number.isFinite(duration) && duration > 0 ? duration : null,
    is_animated: Number.isFinite(frameCount) && frameCount > 1 && Number.isFinite(duration) && duration > 0.05,
  };
}

function normalizeAnimatedImage(sourcePath, targetPath) {
  execFileSync(
    "ffmpeg",
    [
      "-v", "error", "-y",
      "-i", sourcePath,
      "-an",
      "-vf", "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=lanczos,format=yuv420p",
      "-c:v", "libx264",
      "-preset", "medium",
      "-crf", "20",
      "-movflags", "+faststart",
      targetPath,
    ],
    { stdio: ["ignore", "pipe", "pipe"], maxBuffer: 32 * 1024 * 1024 },
  );
}

function probeVisualSource(filePath) {
  const extension = extname(filePath).toLowerCase();
  if ([".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"].includes(extension)) {
    const image = probeImage(filePath);
    return { media_type: "image", ...image, duration_seconds: null };
  }
  if ([".mp4", ".m4v", ".mov", ".webm"].includes(extension)) {
    const video = probeVideoSource(filePath);
    return { media_type: "video", ...video };
  }
  try {
    const video = probeVideoSource(filePath);
    return { media_type: "video", ...video };
  } catch {
    const image = probeImage(filePath);
    return { media_type: "image", ...image, duration_seconds: null };
  }
}

function normalizeImage(sourcePath, targetPath) {
  execFileSync(
    "ffmpeg",
    [
      "-v",
      "error",
      "-y",
      "-i",
      sourcePath,
      "-vf",
      "scale=1920:1920:force_original_aspect_ratio=decrease",
      "-frames:v",
      "1",
      "-q:v",
      "2",
      targetPath,
    ],
    {
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
}

function wrapFallbackText(value) {
  if (typeof value !== "string") {
    throw new HttpError(400, "invalid_text", "text must be a string");
  }

  const normalized = value.replace(/\s+/gu, " ").trim();

  if (normalized.length === 0 || normalized.length > 500) {
    throw new HttpError(
      400,
      "invalid_text",
      "text must contain between 1 and 500 characters",
    );
  }

  const words = normalized.split(" ");
  const lines = [];
  let current = "";

  for (const word of words) {
    const candidate = current.length === 0 ? word : `${current} ${word}`;

    if (candidate.length <= 30) {
      current = candidate;
      continue;
    }

    if (current.length > 0) {
      lines.push(current);
    }

    current = word;
  }

  if (current.length > 0) {
    lines.push(current);
  }

  return lines.slice(0, 12).join("\n");
}

async function storeAudio(request, response) {
  const body = await readJsonBody(request);

  const { job_id: jobId, scene_number: sceneNumber, audio_base64: audioBase64 } =
    body;

  const audio = decodeAudioBase64(audioBase64);
  const { relativePath, absolutePath } = buildAudioPath(jobId, sceneNumber);
  const directoryPath = dirname(absolutePath);
  const temporaryPath = `${absolutePath}.tmp-${randomUUID()}`;

  await mkdir(directoryPath, { recursive: true });

  try {
    await writeFile(temporaryPath, audio, { flag: "wx" });

    const durationSeconds = probeDurationSeconds(temporaryPath);

    await rename(temporaryPath, absolutePath);

    sendJson(response, 200, {
      audio_path: relativePath,
      duration_seconds: durationSeconds,
      bytes: audio.length,
    });
  } catch (error) {
    await rm(temporaryPath, { force: true }).catch(() => {});

    if (error instanceof HttpError) {
      throw error;
    }

    throw new HttpError(
      422,
      "invalid_audio",
      `Audio could not be stored and validated: ${error.message}`,
    );
  }
}

async function storeContinuousVoiceover(request, response) {
  const body = await readJsonBody(request);
  const jobId = String(body.job_id ?? "").trim().toLowerCase();
  const mimeType = String(body.mime_type ?? "").trim().toLowerCase();
  const audio = decodeAudioBase64(body.audio_base64);
  if (!uuidPattern.test(jobId)) {
    throw new HttpError(400, "invalid_job_id", "job_id must be a valid UUID");
  }
  const rateMatch = mimeType.match(/rate=(\d+)/u);
  const channelsMatch = mimeType.match(/channels=(\d+)/u);
  const rate = Number(rateMatch?.[1]);
  const channels = Number(channelsMatch?.[1]);
  if (!mimeType.startsWith("audio/l16") || !Number.isInteger(rate) || rate < 8000 || rate > 96000 || !Number.isInteger(channels) || channels < 1 || channels > 2) {
    throw new HttpError(415, "unsupported_voiceover_type", `Unsupported voiceover format: ${mimeType || "missing"}`);
  }
  const { relativePath, absolutePath } = buildContinuousVoiceoverPath(jobId);
  const directoryPath = dirname(absolutePath);
  const rawPath = `${absolutePath}.raw-${randomUUID()}`;
  const wavPath = `${absolutePath}.tmp-${randomUUID()}.wav`;
  await mkdir(directoryPath, { recursive: true });
  try {
    await writeFile(rawPath, audio, { flag: "wx" });
    execFileSync("ffmpeg", [
      "-v", "error", "-y",
      "-f", "s16le", "-ar", String(rate), "-ac", String(channels), "-i", rawPath,
      "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", wavPath,
    ], { stdio: ["ignore", "pipe", "pipe"], maxBuffer: 16 * 1024 * 1024 });
    const durationSeconds = probeDurationSeconds(wavPath);
    const outputStat = await stat(wavPath);
    await rename(wavPath, absolutePath);
    await rm(rawPath, { force: true });
    sendJson(response, 200, {
      voiceover_path: relativePath,
      media_type: "audio",
      codec_name: "pcm_s16le",
      sample_rate: 48000,
      channels: 2,
      duration_seconds: durationSeconds,
      bytes: outputStat.size,
    });
  } catch (error) {
    await rm(rawPath, { force: true }).catch(() => {});
    await rm(wavPath, { force: true }).catch(() => {});
    if (error instanceof HttpError) throw error;
    throw new HttpError(422, "invalid_voiceover", `Continuous voiceover could not be stored: ${error.message}`);
  }
}

async function synthesizeFreeFallbackVoiceover(request, response) {
  const body = await readJsonBody(request);
  const jobId = String(body.job_id ?? "").trim().toLowerCase();
  const languageCode = String(body.language_code ?? "").trim().toLowerCase();
  const narration = String(body.text ?? "").replace(/\s+/gu, " ").trim();
  const targetDurationSeconds = Number(body.target_duration_seconds);

  if (!uuidPattern.test(jobId)) {
    throw new HttpError(400, "invalid_job_id", "job_id must be a valid UUID");
  }
  const voiceConfig = freeFallbackVoices[languageCode];
  if (!voiceConfig) {
    throw new HttpError(400, "unsupported_fallback_language", `Unsupported fallback TTS language: ${languageCode || "missing"}`);
  }
  if (narration.length === 0 || narration.length > 12000) {
    throw new HttpError(400, "invalid_fallback_narration", "text must contain between 1 and 12000 characters");
  }
  if (!Number.isFinite(targetDurationSeconds) || targetDurationSeconds <= 0 || targetDurationSeconds > 120) {
    throw new HttpError(400, "invalid_target_duration", "target_duration_seconds must be between 1 and 120");
  }

  const providerBudgetMilliseconds = edgeProviderBudgetMilliseconds(targetDurationSeconds);
  const { relativePath, absolutePath } = buildContinuousVoiceoverPath(jobId);
  const directoryPath = dirname(absolutePath);
  const sourcePath = `${absolutePath}.edge-${randomUUID()}.mp3`;
  const wavPath = `${absolutePath}.edge-${randomUUID()}.wav`;
  await mkdir(directoryPath, { recursive: true });

  try {
    await rm(sourcePath, { force: true }).catch(() => {});
    const tts = new EdgeTTS({
      voice: voiceConfig.voice,
      lang: voiceConfig.locale,
      outputFormat: "audio-24khz-48kbitrate-mono-mp3",
      rate: "default",
      pitch: "default",
      volume: "default",
      timeout: providerBudgetMilliseconds,
    });
    await tts.ttsPromise(narration, sourcePath);
    const sourceStat = await stat(sourcePath);
    if (!sourceStat.isFile() || sourceStat.size <= 0) {
      throw new Error("Edge Read Aloud returned an empty audio file");
    }

    const sourceDuration = probeDurationSeconds(sourcePath);
    const ffmpegArgs = [
      "-v", "error", "-y", "-i", sourcePath,
      "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", wavPath,
    ];
    execFileSync("ffmpeg", ffmpegArgs, { stdio: ["ignore", "pipe", "pipe"], maxBuffer: 16 * 1024 * 1024 });

    const durationSeconds = probeDurationSeconds(wavPath);
    if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) {
      throw new Error("Edge Read Aloud normalized audio duration is invalid");
    }
    const outputStat = await stat(wavPath);
    await rename(wavPath, absolutePath);
    await rm(sourcePath, { force: true });

    sendJson(response, 200, {
      voiceover_path: relativePath,
      media_type: "audio",
      codec_name: "pcm_s16le",
      sample_rate: 48000,
      channels: 2,
      duration_seconds: durationSeconds,
      bytes: outputStat.size,
      provider: "microsoft_edge_readaloud",
      model: "edge_neural",
      voice: voiceConfig.voice,
      rate_percent: 0,
      post_tempo_factor: 1,
      source_duration_seconds: sourceDuration,
      provider_budget_ms: providerBudgetMilliseconds,
    });
  } catch (error) {
    await rm(sourcePath, { force: true }).catch(() => {});
    await rm(wavPath, { force: true }).catch(() => {});
    if (error instanceof HttpError) throw error;
    throw new HttpError(502, "free_fallback_tts_failed", `Free fallback TTS failed: ${String(error?.message ?? error)}`);
  }
}

async function storeVisual(request, response, requestUrl, { slotParameter = "scene_number", slotPrefix = "scene" } = {}) {
  const jobId = String(requestUrl.searchParams.get("job_id") ?? "").trim().toLowerCase();
  const slotNumber = Number(requestUrl.searchParams.get(slotParameter));
  const contentType = String(request.headers["content-type"] ?? "").split(";", 1)[0].trim().toLowerCase();
  validateJobAndScene(jobId, slotNumber);
  const isImage = supportedImageTypes.has(contentType);
  const isVideo = supportedVideoTypes.has(contentType);
  if (!isImage && !isVideo) {
    throw new HttpError(415, "unsupported_visual_type", `Unsupported visual Content-Type: ${contentType || "missing"}`);
  }
  const visual = await readBody(request, maxVisualBodyBytes);
  const stagingTarget = buildVisualPath(jobId, slotNumber, "jpg", slotPrefix);
  const directoryPath = dirname(stagingTarget.absolutePath);
  const sourcePath = `${directoryPath}/.scene-${String(slotNumber).padStart(2, "0")}.source-${randomUUID()}`;
  await mkdir(directoryPath, { recursive: true });
  await writeFile(sourcePath, visual, { flag: "wx" });
  let normalizedPath = null;
  try {
    let sourceProbe;
    let normalizedProbe;
    let storedPath;
    let storedMediaType;
    let target;
    if (isVideo) {
      sourceProbe = probeVideoSource(sourcePath);
      normalizedProbe = sourceProbe;
      storedPath = sourcePath;
      storedMediaType = "video";
      target = buildVisualPath(jobId, slotNumber, "mp4", slotPrefix);
    } else if (contentType === "image/gif") {
      const gifProbe = probeAnimatedImage(sourcePath);
      sourceProbe = gifProbe;
      if (gifProbe.is_animated) {
        target = buildVisualPath(jobId, slotNumber, "mp4", slotPrefix);
        normalizedPath = `${target.absolutePath}.normalized-${randomUUID()}.mp4`;
        normalizeAnimatedImage(sourcePath, normalizedPath);
        normalizedProbe = probeVideoSource(normalizedPath);
        storedPath = normalizedPath;
        storedMediaType = "video";
      } else {
        target = buildVisualPath(jobId, slotNumber, "jpg", slotPrefix);
        normalizedPath = `${target.absolutePath}.normalized-${randomUUID()}.jpg`;
        normalizeImage(sourcePath, normalizedPath);
        normalizedProbe = { ...probeImage(normalizedPath), duration_seconds: null };
        storedPath = normalizedPath;
        storedMediaType = "image";
      }
    } else if (contentType === "image/svg+xml") {
      const metadata = await sharp(visual).metadata();
      const width = Number(metadata.width), height = Number(metadata.height);
      if (!Number.isInteger(width) || width <= 0 || !Number.isInteger(height) || height <= 0) throw new Error("SVG metadata did not return valid dimensions");
      sourceProbe = { codec_name: "svg", width, height, pix_fmt: null, duration_seconds: null };
      target = buildVisualPath(jobId, slotNumber, "jpg", slotPrefix);
      normalizedPath = `${target.absolutePath}.normalized-${randomUUID()}.jpg`;
      await sharp(visual, { density: 192 }).flatten({ background: "#ffffff" }).resize({ width: 1920, height: 1920, fit: "inside", withoutEnlargement: false }).jpeg({ quality: 92, chromaSubsampling: "4:4:4" }).toFile(normalizedPath);
      normalizedProbe = { ...probeImage(normalizedPath), duration_seconds: null };
      storedPath = normalizedPath;
      storedMediaType = "image";
    } else {
      sourceProbe = { ...probeImage(sourcePath), duration_seconds: null };
      target = buildVisualPath(jobId, slotNumber, "jpg", slotPrefix);
      normalizedPath = `${target.absolutePath}.normalized-${randomUUID()}.jpg`;
      normalizeImage(sourcePath, normalizedPath);
      normalizedProbe = { ...probeImage(normalizedPath), duration_seconds: null };
      storedPath = normalizedPath;
      storedMediaType = "image";
    }
    const storedStat = await stat(storedPath);
    await rename(storedPath, target.absolutePath);
    if (storedPath !== sourcePath) await rm(sourcePath, { force: true });
    sendJson(response, 200, {
      visual_path: target.relativePath,
      media_type: storedMediaType,
      source_content_type: contentType,
      source_width: sourceProbe.width,
      source_height: sourceProbe.height,
      source_duration_seconds: sourceProbe.duration_seconds ?? null,
      width: normalizedProbe.width,
      height: normalizedProbe.height,
      duration_seconds: normalizedProbe.duration_seconds ?? null,
      codec_name: normalizedProbe.codec_name,
      bytes: storedStat.size,
    });
  } catch (error) {
    await rm(sourcePath, { force: true }).catch(() => {});
    if (normalizedPath) await rm(normalizedPath, { force: true }).catch(() => {});
    if (error instanceof HttpError) throw error;
    throw new HttpError(422, "invalid_visual", `Visual could not be stored and normalized: ${error.message}`);
  }
}

async function averageHashHex(buffer) {
  const { data, info } = await sharp(buffer)
    .flatten({ background: "#ffffff" })
    .grayscale()
    .resize(16, 16, { fit: "fill" })
    .raw()
    .toBuffer({ resolveWithObject: true });
  if (info.channels !== 1 || data.length !== 256) throw new Error(`Unexpected perceptual hash shape ${info.width}x${info.height}x${info.channels}`);
  let sum = 0;
  for (const value of data) sum += value;
  const average = sum / data.length;
  let hex = "";
  for (let offset = 0; offset < data.length; offset += 4) {
    let nibble = 0;
    for (let bit = 0; bit < 4; bit += 1) nibble = (nibble << 1) | (data[offset + bit] >= average ? 1 : 0);
    hex += nibble.toString(16);
  }
  return hex;
}

async function rankVisualCandidates(request, response) {
  const body = await readJsonBody(request);
  const query = String(body.query ?? "").replace(/\s+/gu, " ").trim();
  const candidates = body.candidates;

  if (query.length === 0 || query.length > 200) {
    throw new HttpError(
      400,
      "invalid_rank_query",
      "query must contain between 1 and 200 characters",
    );
  }

  if (
    !Array.isArray(candidates) ||
    candidates.length === 0 ||
    candidates.length > maxRankCandidates
  ) {
    throw new HttpError(
      400,
      "invalid_rank_candidates",
      `candidates must contain between 1 and ${maxRankCandidates} items`,
    );
  }

  const normalizedCandidates = candidates.map((candidate, index) => {
    if (candidate === null || typeof candidate !== "object" || Array.isArray(candidate)) {
      throw new HttpError(
        400,
        "invalid_rank_candidate",
        `candidate ${index + 1} must be an object`,
      );
    }

    const candidateId = String(candidate.candidate_id ?? "").trim();

    if (candidateId.length === 0 || candidateId.length > 1000) {
      throw new HttpError(
        400,
        "invalid_candidate_id",
        `candidate ${index + 1} candidate_id is invalid`,
      );
    }

    const rawPreviewUrls = Array.isArray(candidate.preview_urls)
      ? candidate.preview_urls
      : [candidate.preview_url];

    if (
      rawPreviewUrls.length === 0 ||
      rawPreviewUrls.length > maxRankPreviewsPerCandidate
    ) {
      throw new HttpError(
        400,
        "invalid_candidate_previews",
        `candidate ${index + 1} must contain between 1 and ${maxRankPreviewsPerCandidate} preview URLs`,
      );
    }

    const previewUrls = [
      ...new Set(rawPreviewUrls.map((value) => validatePreviewUrl(value))),
    ];

    return {
      candidate_id: candidateId,
      preview_urls: previewUrls,
    };
  });

  if (new Set(normalizedCandidates.map((candidate) => candidate.candidate_id)).size !== normalizedCandidates.length) {
    throw new HttpError(
      400,
      "duplicate_candidate_id",
      "candidate_id values must be unique",
    );
  }

  const requestedPreviewCount = normalizedCandidates.reduce(
    (total, candidate) => total + candidate.preview_urls.length,
    0,
  );

  if (requestedPreviewCount > maxRankPreviewImages) {
    throw new HttpError(
      400,
      "too_many_rank_previews",
      `candidate previews must contain at most ${maxRankPreviewImages} images`,
    );
  }

  try {
    await mkdir(siglipCacheDir, { recursive: true });
    const classifier = await getSiglipPipeline();
    const previewEntries = normalizedCandidates.flatMap((candidate) =>
      candidate.preview_urls.map((previewUrl, previewIndex) => ({
        candidate_id: candidate.candidate_id,
        preview_index: previewIndex,
        preview_url: previewUrl,
      })),
    );
    const rankablePreviewEntries = [];
    const previewImages = [];
    const rejected = [];

    const decodedPreviews = await Promise.all(
      previewEntries.map(async (entry) => {
        try {
          const previewResult = await fetchPreviewCached(entry.preview_url);

          if (!previewResult.ok || !previewResult.buffer) {
            throw new Error(`HTTP ${previewResult.status}`);
          }

          const { data, info } = await sharp(previewResult.buffer)
            .flatten({ background: "#ffffff" })
            .toColourspace("srgb")
            .removeAlpha()
            .raw()
            .toBuffer({ resolveWithObject: true });

          if (info.channels !== 3) {
            throw new Error(`normalized channels=${info.channels}`);
          }

          const visualHash = await averageHashHex(previewResult.buffer);
          return {
            entry,
            image: new RawImage(data, info.width, info.height, info.channels),
            visualHash,
            rejectionReason: null,
          };
        } catch (error) {
          return {
            entry,
            image: null,
            rejectionReason: String(error.message ?? error).slice(0, 300),
          };
        }
      }),
    );

    for (const decoded of decodedPreviews) {
      if (decoded.image) {
        rankablePreviewEntries.push({ ...decoded.entry, visual_hash: decoded.visualHash });
        previewImages.push(decoded.image);
      } else {
        rejected.push({
          candidate_id: decoded.entry.candidate_id,
          preview_index: decoded.entry.preview_index,
          reason: decoded.rejectionReason,
        });
      }
    }

    if (rankablePreviewEntries.length === 0) {
      throw new Error("No candidate preview could be decoded for semantic ranking");
    }

    const rawOutput = await runSiglipInference(classifier, previewImages, query);

    const perImageOutput =
      rankablePreviewEntries.length === 1 &&
      Array.isArray(rawOutput) &&
      !Array.isArray(rawOutput[0])
        ? [rawOutput]
        : rawOutput;

    if (!Array.isArray(perImageOutput) || perImageOutput.length !== rankablePreviewEntries.length) {
      throw new Error("SigLIP returned an unexpected batch shape");
    }

    const aggregated = new Map(
      normalizedCandidates.map((candidate) => [
        candidate.candidate_id,
        {
          candidate_id: candidate.candidate_id,
          score: -1,
          preview_count: candidate.preview_urls.length,
          ranked_preview_count: 0,
          best_preview_index: null,
          visual_hash: null,
        },
      ]),
    );

    for (let index = 0; index < rankablePreviewEntries.length; index += 1) {
      const entry = rankablePreviewEntries[index];
      const score = Number(perImageOutput[index]?.[0]?.score);

      if (!Number.isFinite(score) || score < 0 || score > 1) {
        throw new Error(
          `SigLIP returned an invalid score for candidate ${entry.candidate_id}`,
        );
      }

      const candidate = aggregated.get(entry.candidate_id);
      candidate.ranked_preview_count += 1;

      if (score > candidate.score) {
        candidate.score = score;
        candidate.best_preview_index = entry.preview_index;
        candidate.visual_hash = entry.visual_hash;
      }
    }

    const ranked = [...aggregated.values()]
      .filter((candidate) => candidate.ranked_preview_count > 0)
      .sort((left, right) => right.score - left.score)
      .map((candidate, index) => ({ ...candidate, rank: index + 1 }));

    sendJson(response, 200, {
      model: siglipModel,
      dtype: siglipDtype,
      query,
      candidate_count: ranked.length,
      requested_candidate_count: normalizedCandidates.length,
      rejected_candidate_count: normalizedCandidates.length - ranked.length,
      requested_preview_count: requestedPreviewCount,
      ranked_preview_count: rankablePreviewEntries.length,
      rejected_preview_count: rejected.length,
      rejected,
      ranked,
    });
  } catch (error) {
    if (error instanceof HttpError) {
      throw error;
    }

    throw new HttpError(
      422,
      "visual_ranking_failed",
      `Visual candidates could not be ranked: ${error.message}`,
    );
  }
}

async function createVisualContactSheet(request, response) {
  const body = await readJsonBody(request);
  const sceneNumber = Number(body.scene_number);
  const candidates = body.candidates;

  if (!Number.isInteger(sceneNumber) || sceneNumber < 1 || sceneNumber > 100) {
    throw new HttpError(400, "invalid_contact_sheet_scene", "scene_number must be a positive integer");
  }

  if (!Array.isArray(candidates) || candidates.length < 1 || candidates.length > maxRankCandidates) {
    throw new HttpError(
      400,
      "invalid_contact_sheet_candidates",
      `candidates must contain between 1 and ${maxRankCandidates} items`,
    );
  }

  const normalized = candidates.map((candidate, index) => {
    if (candidate === null || typeof candidate !== "object" || Array.isArray(candidate)) {
      throw new HttpError(400, "invalid_contact_sheet_candidate", `candidate ${index + 1} must be an object`);
    }
    const candidateId = String(candidate.candidate_id ?? "").trim();
    if (!candidateId || candidateId.length > 1000) {
      throw new HttpError(400, "invalid_contact_sheet_candidate_id", `candidate ${index + 1} candidate_id is invalid`);
    }
    return {
      candidate_id: candidateId,
      preview_url: validatePreviewUrl(candidate.preview_url),
    };
  });

  if (new Set(normalized.map((candidate) => candidate.candidate_id)).size !== normalized.length) {
    throw new HttpError(400, "duplicate_contact_sheet_candidate", "candidate_id values must be unique");
  }

  const decoded = await Promise.all(normalized.map(async (candidate) => {
    try {
      const previewResult = await fetchPreviewCached(candidate.preview_url);
      if (!previewResult.ok || !previewResult.buffer) return null;
      const image = await sharp(previewResult.buffer)
        .flatten({ background: "#111111" })
        .toColourspace("srgb")
        .resize(240, 160, { fit: "cover", position: "attention" })
        .jpeg({ quality: 82, chromaSubsampling: "4:2:0" })
        .toBuffer();
      return { candidate, image };
    } catch {
      return null;
    }
  }));

  const usable = decoded.filter(Boolean);
  if (!usable.length) {
    throw new HttpError(422, "contact_sheet_empty", "No candidate preview could be decoded");
  }

  const columns = Math.min(3, usable.length);
  const rows = Math.ceil(usable.length / columns);
  const tileWidth = 240;
  const tileHeight = 160;
  const composites = [];
  const returnedCandidates = [];

  for (let index = 0; index < usable.length; index += 1) {
    const choice = index + 1;
    const x = (index % columns) * tileWidth;
    const y = Math.floor(index / columns) * tileHeight;
    const badge = Buffer.from(
      `<svg width="62" height="36" xmlns="http://www.w3.org/2000/svg"><rect width="62" height="36" rx="7" fill="rgba(0,0,0,0.82)"/><text x="31" y="25" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-size="21" font-weight="700" fill="#fff">${choice}</text></svg>`,
    );
    composites.push({ input: usable[index].image, left: x, top: y });
    composites.push({ input: badge, left: x + 7, top: y + 7 });
    returnedCandidates.push({
      choice,
      candidate_id: usable[index].candidate.candidate_id,
    });
  }

  const sheet = await sharp({
    create: {
      width: columns * tileWidth,
      height: rows * tileHeight,
      channels: 3,
      background: "#111111",
    },
  })
    .composite(composites)
    .jpeg({ quality: 78, chromaSubsampling: "4:2:0" })
    .toBuffer();

  sendJson(response, 200, {
    scene_number: sceneNumber,
    mime_type: "image/jpeg",
    width: columns * tileWidth,
    height: rows * tileHeight,
    candidates: returnedCandidates,
    image_base64: sheet.toString("base64"),
  });
}

async function discoverVisuals(request, response) {
  const body = await readJsonBody(request);
  try {
    const result = await discoverVisualCandidates(buildVisualDiscoveryOptions(body, {
      pixabayApiKey: process.env.PIXABAY_API_KEY ?? "",
      pexelsApiKey: process.env.PEXELS_API_KEY ?? "",
    }));
    sendJson(response, 200, result);
  } catch (error) {
    throw new HttpError(422, "visual_discovery_failed", `Visual discovery failed: ${String(error?.message ?? error)}`);
  }
}

async function createVisualFallback(request, response) {
  await readJsonBody(request);
  throw new HttpError(
    409,
    "visual_fallback_disabled",
    "The clean rebuild does not generate descriptive or topic-specific visual fallbacks. Visual sourcing must select a trustworthy provider asset or fail closed",
  );
}

function buildRenderPath(jobId) {
  if (!uuidPattern.test(jobId)) {
    throw new HttpError(400, "invalid_job_id", "job_id must be a valid UUID");
  }

  const relativePath = `jobs/${jobId.toLowerCase()}/render/final.mp4`;
  const absolutePath = resolve(dataRoot, relativePath);

  if (
    absolutePath !== dataRoot &&
    !absolutePath.startsWith(`${dataRoot}${sep}`)
  ) {
    throw new HttpError(400, "invalid_render_path", "Resolved render path is unsafe");
  }

  return { relativePath, absolutePath };
}

function resolvePersistedMediaPath(jobId, value, kind) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new HttpError(
      400,
      `invalid_${kind}_path`,
      `${kind}_path must be a non-empty relative path`,
    );
  }

  const normalized = value.trim().replaceAll("\\", "/");
  const expectedPrefix = `jobs/${jobId.toLowerCase()}/`;
  const expectedSegment = kind === "audio" ? "voiceover/" : "visuals/";

  if (
    normalized.startsWith("/") ||
    normalized.includes("../") ||
    !normalized.startsWith(`${expectedPrefix}${expectedSegment}`)
  ) {
    throw new HttpError(
      400,
      `invalid_${kind}_path`,
      `${kind}_path does not belong to job ${jobId}`,
    );
  }

  const absolutePath = resolve(dataRoot, normalized);

  if (
    absolutePath === dataRoot ||
    !absolutePath.startsWith(`${dataRoot}${sep}`)
  ) {
    throw new HttpError(
      400,
      `invalid_${kind}_path`,
      `Resolved ${kind}_path is unsafe`,
    );
  }

  return { relativePath: normalized, absolutePath };
}

function wrapSubtitleText(value) {
  if (typeof value !== "string") {
    throw new HttpError(400, "invalid_narration", "narration must be a string");
  }

  const normalized = value.replace(/\s+/gu, " ").trim();

  if (normalized.length === 0 || normalized.length > 1200) {
    throw new HttpError(
      400,
      "invalid_narration",
      "narration must contain between 1 and 1200 characters",
    );
  }

  const words = normalized.split(" ");
  const lines = [];
  let current = "";

  for (const word of words) {
    const candidate = current.length === 0 ? word : `${current} ${word}`;

    if (candidate.length <= 34) {
      current = candidate;
      continue;
    }

    if (current.length > 0) {
      lines.push(current);
    }

    current = word;
  }

  if (current.length > 0) {
    lines.push(current);
  }

  return lines.slice(0, 4).join("\\N");
}

function escapeAssText(value) {
  return wrapSubtitleText(value)
    .replaceAll("\\", "\\\\")
    .replaceAll("{", "\\{")
    .replaceAll("}", "\\}")
    .replaceAll("\\\\N", "\\N");
}

function assTime(seconds) {
  const centiseconds = Math.max(0, Math.round(Number(seconds) * 100));
  const hours = Math.floor(centiseconds / 360000);
  const minutes = Math.floor((centiseconds % 360000) / 6000);
  const wholeSeconds = Math.floor((centiseconds % 6000) / 100);
  const fraction = centiseconds % 100;

  return `${hours}:${String(minutes).padStart(2, "0")}:${String(wholeSeconds).padStart(2, "0")}.${String(fraction).padStart(2, "0")}`;
}

function probeRenderedVideo(filePath) {
  const output = execFileSync(
    "ffprobe",
    [
      "-v",
      "error",
      "-show_entries",
      "format=duration:stream=index,codec_type,codec_name,width,height,pix_fmt,sample_rate,channels,duration",
      "-of",
      "json",
      filePath,
    ],
    {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
    },
  );

  const parsed = JSON.parse(output);
  const video = parsed.streams?.find((stream) => stream.codec_type === "video");
  const audio = parsed.streams?.find((stream) => stream.codec_type === "audio");
  const durationSeconds = Number(parsed.format?.duration);
  const videoDurationSeconds = Number(video?.duration);
  const audioDurationSeconds = Number(audio?.duration);

  if (
    !video ||
    !audio ||
    video.codec_name !== "h264" ||
    Number(video.width) !== 1080 ||
    Number(video.height) !== 1920 ||
    audio.codec_name !== "aac" ||
    !Number.isFinite(durationSeconds) ||
    durationSeconds <= 0 ||
    !Number.isFinite(videoDurationSeconds) ||
    videoDurationSeconds <= 0 ||
    !Number.isFinite(audioDurationSeconds) ||
    audioDurationSeconds <= 0
  ) {
    throw new Error("ffprobe did not return the required H.264/AAC 1080x1920 output with stream durations");
  }

  return {
    duration_seconds: durationSeconds,
    video_duration_seconds: videoDurationSeconds,
    audio_duration_seconds: audioDurationSeconds,
    width: Number(video.width),
    height: Number(video.height),
    video_codec: video.codec_name,
    video_pix_fmt: video.pix_fmt ?? null,
    audio_codec: audio.codec_name,
    audio_sample_rate: Number(audio.sample_rate) || null,
    audio_channels: Number(audio.channels) || null,
  };
}

function sampleRenderedFrameHash(videoPath, seconds) {
  const time = Math.max(0, Number(seconds));
  const buffer = execFileSync(
    "ffmpeg",
    [
      "-v", "error",
      "-ss", time.toFixed(6),
      "-i", videoPath,
      "-frames:v", "1",
      "-vf", "crop=iw:floor(ih*0.65):0:0,scale=16:16,format=gray",
      "-f", "rawvideo",
      "pipe:1",
    ],
    { stdio: ["ignore", "pipe", "pipe"], maxBuffer: 1024 * 1024 },
  );
  if (!Buffer.isBuffer(buffer) || buffer.length !== 256) throw new Error(`Unexpected rendered frame sample size: ${buffer?.length ?? 0}`);
  let sum = 0;
  for (const value of buffer) sum += value;
  const average = sum / buffer.length;
  return [...buffer].map((value) => value >= average ? 1 : 0);
}

function inspectRenderedVisualDiversity(videoPath, beats, requiredUniqueAssetCount) {
  const hashes = beats.map((beat) => sampleRenderedFrameHash(videoPath, (Number(beat.start_seconds) + Number(beat.end_seconds)) / 2));
  const clusters = clusterAverageHashes(hashes, 18);
  const renderedVisualStateCount = clusters.length;
  if (renderedVisualStateCount < requiredUniqueAssetCount) {
    throw new HttpError(
      422,
      "render_visual_state_diversity_failed",
      `Rendered visual states ${renderedVisualStateCount}/${requiredUniqueAssetCount} are insufficient`,
    );
  }
  return {
    rendered_visual_state_count: renderedVisualStateCount,
    required_rendered_visual_state_count: requiredUniqueAssetCount,
    rendered_visual_clusters: clusters.map((cluster) => cluster.map((index) => Number(beats[index].beat_number))),
  };
}


function inspectRenderedVisualShotDiversity(videoPath, shots) {
  const hashes = shots.map((shot) => sampleRenderedFrameHash(videoPath, (Number(shot.start_seconds) + Number(shot.end_seconds)) / 2));
  const clusters = clusterAverageHashes(hashes, 18);
  const clusterByShot = new Array(shots.length);
  for (let clusterIndex = 0; clusterIndex < clusters.length; clusterIndex += 1) {
    for (const shotIndex of clusters[clusterIndex]) clusterByShot[shotIndex] = clusterIndex;
  }
  let adjacent = 0;
  const counts = new Map();
  const durations = new Map();
  let totalDuration = 0;
  for (let index = 0; index < shots.length; index += 1) {
    const cluster = clusterByShot[index];
    const duration = Number(shots[index].duration_seconds);
    if (!Number.isInteger(cluster) || !Number.isFinite(duration) || duration <= 0) throw new Error("Rendered shot inspection produced invalid state");
    if (index > 0 && cluster === clusterByShot[index - 1]) adjacent += 1;
    counts.set(cluster, (counts.get(cluster) ?? 0) + 1);
    durations.set(cluster, (durations.get(cluster) ?? 0) + duration);
    totalDuration += duration;
  }
  const stateCount = clusters.length;
  const requiredStateCount = requiredRenderedShotStateCount(shots.length, 2);
  const maxOccurrence = Math.max(...counts.values());
  const maxShare = Math.max(...durations.values()) / totalDuration;
  if (stateCount < requiredStateCount || adjacent !== 0 || maxOccurrence > 2 || !Number.isFinite(maxShare) || maxShare > 0.34) {
    throw new HttpError(
      422,
      "render_visual_state_diversity_failed",
      `Rendered shot states failed: states=${stateCount}/${requiredStateCount}, adjacent=${adjacent}, max_occurrence=${maxOccurrence}, max_share=${maxShare}`,
    );
  }
  return {
    rendered_visual_state_count: stateCount,
    required_rendered_visual_state_count: requiredStateCount,
    rendered_adjacent_visual_state_duplicate_count: adjacent,
    rendered_max_visual_state_occurrence_count: maxOccurrence,
    rendered_max_visual_state_duration_share: Number(maxShare.toFixed(4)),
    rendered_visual_clusters: clusters.map((cluster) => cluster.map((index) => Number(shots[index].shot_number))),
  };
}


async function renderVideoV3(request, response) {
  const body = await readJsonBody(request);
  const jobId = String(body.job_id ?? "").trim().toLowerCase();
  const beats = body.beats;
  const shots = body.shots;
  if (!uuidPattern.test(jobId)) throw new HttpError(400, "invalid_job_id", "job_id must be a valid UUID");
  if (!Array.isArray(beats) || beats.length === 0 || beats.length > 100) throw new HttpError(400, "invalid_render_beats", "beats must contain between 1 and 100 subtitle items");
  if (!Array.isArray(shots) || shots.length === 0 || shots.length > 100) throw new HttpError(400, "invalid_render_shots", "shots must contain between 1 and 100 visual items");
  const audioPath = resolvePersistedMediaPath(jobId, body.audio_path, "audio");
  try {
    const audioStat = await stat(audioPath.absolutePath);
    if (!audioStat.isFile()) throw new Error("audio path is not a file");
  } catch {
    throw new HttpError(422, "render_audio_missing", "Continuous voiceover file is missing");
  }
  const measuredAudioDuration = probeDurationSeconds(audioPath.absolutePath);

  const normalizedBeats = [];
  let previousEnd = 0;
  for (let index = 0; index < beats.length; index += 1) {
    const beat = beats[index];
    if (beat === null || typeof beat !== "object" || Array.isArray(beat)) throw new HttpError(400, "invalid_render_beat", `beat ${index + 1} must be an object`);
    const beatNumber = Number(beat.beat_number);
    if (!Number.isInteger(beatNumber) || beatNumber !== index + 1) throw new HttpError(400, "invalid_beat_number", `beat ${index + 1} must be sequential`);
    const start = Number(beat.start_seconds), end = Number(beat.end_seconds), duration = Number(beat.duration_seconds);
    if (!Number.isFinite(start) || !Number.isFinite(end) || !Number.isFinite(duration) || start < 0 || end <= start || duration <= 0 || Math.abs(start - previousEnd) > 0.02 || Math.abs((end - start) - duration) > 0.02) throw new HttpError(400, "invalid_beat_timing", `beat ${beatNumber} timing is invalid`);
    const narration = String(beat.narration ?? "").replace(/\s+/gu, " ").trim();
    if (!narration || narration.length > 1200) throw new HttpError(400, "invalid_narration", `beat ${beatNumber} narration is invalid`);
    normalizedBeats.push({ beat_number: beatNumber, narration, start_seconds: start, end_seconds: end, duration_seconds: duration });
    previousEnd = end;
  }
  if (Math.abs(previousEnd - measuredAudioDuration) > 0.35) throw new HttpError(422, "beat_audio_duration_mismatch", `Final beat end ${previousEnd} differs from voiceover ${measuredAudioDuration}`);

  const normalizedShots = [];
  previousEnd = 0;
  for (let index = 0; index < shots.length; index += 1) {
    const shot = shots[index];
    if (shot === null || typeof shot !== "object" || Array.isArray(shot)) throw new HttpError(400, "invalid_render_shot", `shot ${index + 1} must be an object`);
    const shotNumber = Number(shot.shot_number);
    if (!Number.isInteger(shotNumber) || shotNumber !== index + 1) throw new HttpError(400, "invalid_shot_number", `shot ${index + 1} must be sequential`);
    const start = Number(shot.start_seconds), end = Number(shot.end_seconds), duration = Number(shot.duration_seconds);
    if (!Number.isFinite(start) || !Number.isFinite(end) || !Number.isFinite(duration) || start < 0 || end <= start || duration <= 0 || Math.abs(start - previousEnd) > 0.02 || Math.abs((end - start) - duration) > 0.02) throw new HttpError(400, "invalid_shot_timing", `shot ${shotNumber} timing is invalid`);
    const assetKey = String(shot.asset_key ?? "").trim();
    const visualClusterKey = String(shot.visual_cluster_key ?? "").trim();
    if (!assetKey) throw new HttpError(400, "invalid_visual_asset_key", `shot ${shotNumber} asset_key is missing`);
    if (!visualClusterKey) throw new HttpError(400, "invalid_visual_cluster_key", `shot ${shotNumber} visual_cluster_key is missing`);
    const visualPath = resolvePersistedMediaPath(jobId, shot.visual_path, "visual");
    try {
      const visualStat = await stat(visualPath.absolutePath);
      if (!visualStat.isFile()) throw new Error("visual is not a file");
    } catch {
      throw new HttpError(422, "render_input_missing", `shot ${shotNumber} visual file is missing`);
    }
    const visualProbe = probeVisualSource(visualPath.absolutePath);
    normalizedShots.push({
      shot_number: shotNumber,
      segment_number: Number(shot.segment_number),
      segment_shot_number: Number(shot.segment_shot_number),
      visual_kind: String(shot.visual_kind ?? ""),
      asset_key: assetKey,
      visual_cluster_key: visualClusterKey,
      visual_path: visualPath,
      visual_media_type: visualProbe.media_type,
      start_seconds: start,
      end_seconds: end,
      duration_seconds: duration,
    });
    previousEnd = end;
  }
  if (Math.abs(previousEnd - measuredAudioDuration) > 0.35) throw new HttpError(422, "shot_audio_duration_mismatch", `Final shot end ${previousEnd} differs from voiceover ${measuredAudioDuration}`);

  let sequenceQuality;
  try {
    sequenceQuality = evaluateVisualShotSequence(normalizedShots);
  } catch (error) {
    throw new HttpError(422, "render_visual_sequence_invalid", `Visual shot sequence is invalid: ${error.message}`);
  }
  if (!sequenceQuality.pass) {
    throw new HttpError(
      422,
      "render_visual_sequence_diversity_failed",
      `Visual shots failed: states=${sequenceQuality.unique_visual_cluster_count}/${sequenceQuality.required_unique_visual_cluster_count}, assets=${sequenceQuality.unique_asset_count}/${sequenceQuality.shot_count}, adjacent=${sequenceQuality.adjacent_visual_cluster_duplicate_count}, max_occurrence=${sequenceQuality.max_visual_cluster_occurrence_count}, max_share=${sequenceQuality.max_visual_cluster_duration_share}`,
    );
  }

  const { relativePath, absolutePath } = buildRenderPath(jobId);
  const renderDirectory = dirname(absolutePath);
  const workDirectory = `${renderDirectory}/.tmp-${randomUUID()}`;
  const subtitlePath = `${workDirectory}/subtitles.ass`;
  const temporaryOutputPath = `${workDirectory}/final.mp4`;
  await mkdir(workDirectory, { recursive: true });
  try {
    const dialogueLines = normalizedBeats.map((beat) => `Dialogue: 0,${assTime(beat.start_seconds)},${assTime(beat.end_seconds)},Subtitle,,0,0,0,,${escapeAssText(beat.narration)}`);
    const ass = [
      "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
      "[V4+ Styles]", "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
      "Style: Subtitle,DejaVu Sans,58,&H00FFFFFF,&H000000FF,&H00101010,&H78000000,-1,0,0,0,100,100,0,0,1,4,1,2,70,70,165,1", "",
      "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text", ...dialogueLines, "",
    ].join("\n");
    await writeFile(subtitlePath, ass, { encoding: "utf8", flag: "wx" });
    const ffmpegArgs = ["-v", "error", "-y"];
    for (const shot of normalizedShots) {
      if (shot.visual_media_type === "image") ffmpegArgs.push("-framerate", "30", "-i", shot.visual_path.absolutePath);
      else ffmpegArgs.push("-stream_loop", "-1", "-i", shot.visual_path.absolutePath);
    }
    const audioInputIndex = normalizedShots.length;
    ffmpegArgs.push("-i", audioPath.absolutePath);
    const filters = [];
    for (let index = 0; index < normalizedShots.length; index += 1) {
      const shot = normalizedShots[index];
      filters.push(...buildVisualBeatFilters({ index, duration: shot.duration_seconds, isImage: shot.visual_media_type === "image", isFactualGraphic: shot.visual_kind === "factual_graphic" }));
    }
    const concatInputs = normalizedShots.map((_, index) => `[v${index}]`).join("");
    filters.push(`${concatInputs}concat=n=${normalizedShots.length}:v=1:a=0[vcat]`);
    filters.push(`[${audioInputIndex}:a]atrim=0:${measuredAudioDuration.toFixed(6)},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[acat]`);
    filters.push(`[vcat]subtitles=filename=${subtitlePath}:fontsdir=/usr/share/fonts/truetype/dejavu[vout]`);
    ffmpegArgs.push("-filter_complex", filters.join(";"), "-map", "[vout]", "-map", "[acat]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-shortest", temporaryOutputPath);
    execFileSync("ffmpeg", ffmpegArgs, { stdio: ["ignore", "pipe", "pipe"], maxBuffer: 64 * 1024 * 1024 });
    const probe = probeRenderedVideo(temporaryOutputPath);
    if (Math.abs(probe.duration_seconds - measuredAudioDuration) > 0.6) throw new Error(`Rendered container duration ${probe.duration_seconds} differs from voiceover ${measuredAudioDuration}`);
    if (Math.abs(probe.audio_duration_seconds - measuredAudioDuration) > 0.6) throw new Error(`Rendered audio stream duration ${probe.audio_duration_seconds} differs from voiceover ${measuredAudioDuration}`);
    if (Math.abs(probe.video_duration_seconds - measuredAudioDuration) > 0.6) throw new Error(`Rendered video stream duration ${probe.video_duration_seconds} differs from voiceover ${measuredAudioDuration}`);
    const renderedQuality = inspectRenderedVisualShotDiversity(temporaryOutputPath, normalizedShots);
    const visualQuality = { ...sequenceQuality, ...renderedQuality, pre_render_pass: true, pass: true };
    const outputStat = await stat(temporaryOutputPath);
    await mkdir(renderDirectory, { recursive: true });
    await rename(temporaryOutputPath, absolutePath);
    sendJson(response, 200, {
      video_path: relativePath, media_type: "video", width: probe.width, height: probe.height, video_codec: probe.video_codec, video_pix_fmt: probe.video_pix_fmt,
      audio_codec: probe.audio_codec, audio_sample_rate: probe.audio_sample_rate, audio_channels: probe.audio_channels, duration_seconds: probe.duration_seconds,
      video_stream_duration_seconds: probe.video_duration_seconds, audio_stream_duration_seconds: probe.audio_duration_seconds,
      expected_audio_duration_seconds: measuredAudioDuration, subtitles_burned_in: true, visual_quality: visualQuality,
      beat_timings: normalizedBeats.map((beat) => ({ beat_number: beat.beat_number, start_seconds: beat.start_seconds, end_seconds: beat.end_seconds, duration_seconds: beat.duration_seconds })),
      shot_timings: normalizedShots.map((shot) => ({ shot_number: shot.shot_number, segment_number: shot.segment_number, segment_shot_number: shot.segment_shot_number, start_seconds: shot.start_seconds, end_seconds: shot.end_seconds, duration_seconds: shot.duration_seconds, media_type: shot.visual_media_type, asset_key: shot.asset_key, visual_cluster_key: shot.visual_cluster_key })),
      bytes: outputStat.size,
    });
  } catch (error) {
    if (error instanceof HttpError) throw error;
    throw new HttpError(422, "render_failed", `Video could not be rendered: ${error.message}`);
  } finally {
    await rm(workDirectory, { recursive: true, force: true }).catch(() => {});
  }
}

async function renderVideo(request, response) {
  const body = await readJsonBody(request);
  const jobId = String(body.job_id ?? "").trim().toLowerCase();
  const beats = body.beats;
  if (!uuidPattern.test(jobId)) throw new HttpError(400, "invalid_job_id", "job_id must be a valid UUID");
  if (!Array.isArray(beats) || beats.length === 0 || beats.length > 100) throw new HttpError(400, "invalid_render_beats", "beats must contain between 1 and 100 items");
  const audioPath = resolvePersistedMediaPath(jobId, body.audio_path, "audio");
  try {
    const audioStat = await stat(audioPath.absolutePath);
    if (!audioStat.isFile()) throw new Error("audio path is not a file");
  } catch {
    throw new HttpError(422, "render_audio_missing", "Continuous voiceover file is missing");
  }
  const measuredAudioDuration = probeDurationSeconds(audioPath.absolutePath);
  const normalizedBeats = [];
  let previousEnd = 0;
  for (let index = 0; index < beats.length; index += 1) {
    const beat = beats[index];
    if (beat === null || typeof beat !== "object" || Array.isArray(beat)) throw new HttpError(400, "invalid_render_beat", `beat ${index + 1} must be an object`);
    const beatNumber = Number(beat.beat_number);
    if (!Number.isInteger(beatNumber) || beatNumber !== index + 1) throw new HttpError(400, "invalid_beat_number", `beat ${index + 1} must be sequential`);
    const start = Number(beat.start_seconds), end = Number(beat.end_seconds), duration = Number(beat.duration_seconds);
    if (!Number.isFinite(start) || !Number.isFinite(end) || !Number.isFinite(duration) || start < 0 || end <= start || duration <= 0 || Math.abs(start - previousEnd) > 0.2 || Math.abs((end - start) - duration) > 0.2) {
      throw new HttpError(400, "invalid_beat_timing", `beat ${beatNumber} timing is invalid`);
    }
    const narration = String(beat.narration ?? "").replace(/\s+/gu, " ").trim();
    if (!narration || narration.length > 1200) throw new HttpError(400, "invalid_narration", `beat ${beatNumber} narration is invalid`);
    const assetKey = String(beat.asset_key ?? "").trim();
    const visualClusterKey = String(beat.visual_cluster_key ?? "").trim();
    if (!assetKey) throw new HttpError(400, "invalid_visual_asset_key", `beat ${beatNumber} asset_key is missing`);
    if (!visualClusterKey) throw new HttpError(400, "invalid_visual_cluster_key", `beat ${beatNumber} visual_cluster_key is missing`);
    const visualPath = resolvePersistedMediaPath(jobId, beat.visual_path, "visual");
    try {
      const visualStat = await stat(visualPath.absolutePath);
      if (!visualStat.isFile()) throw new Error("visual is not a file");
    } catch {
      throw new HttpError(422, "render_input_missing", `beat ${beatNumber} visual file is missing`);
    }
    const visualProbe = probeVisualSource(visualPath.absolutePath);
    normalizedBeats.push({ beat_number: beatNumber, narration, visual_kind: String(beat.visual_kind ?? ""), asset_key: assetKey, visual_cluster_key: visualClusterKey, visual_path: visualPath, visual_media_type: visualProbe.media_type, start_seconds: start, end_seconds: end, duration_seconds: duration });
    previousEnd = end;
  }
  if (Math.abs(previousEnd - measuredAudioDuration) > 0.35) throw new HttpError(422, "beat_audio_duration_mismatch", `Final beat end ${previousEnd} differs from voiceover ${measuredAudioDuration}`);
  const sequenceQuality = evaluateVisualSequence(normalizedBeats);
  if (!sequenceQuality.pass) {
    throw new HttpError(
      422,
      "render_visual_sequence_diversity_failed",
      `Visual sequence failed perceptual diversity: clusters=${sequenceQuality.unique_visual_cluster_count}/${sequenceQuality.required_unique_visual_cluster_count}, assets=${sequenceQuality.unique_asset_count}, adjacent=${sequenceQuality.adjacent_visual_cluster_duplicate_count}, max_share=${sequenceQuality.max_visual_cluster_duration_share}`,
    );
  }
  const { relativePath, absolutePath } = buildRenderPath(jobId);
  const renderDirectory = dirname(absolutePath);
  const workDirectory = `${renderDirectory}/.tmp-${randomUUID()}`;
  const subtitlePath = `${workDirectory}/subtitles.ass`;
  const temporaryOutputPath = `${workDirectory}/final.mp4`;
  await mkdir(workDirectory, { recursive: true });
  try {
    const dialogueLines = normalizedBeats.map((beat) => `Dialogue: 0,${assTime(beat.start_seconds)},${assTime(beat.end_seconds)},Subtitle,,0,0,0,,${escapeAssText(beat.narration)}`);
    const ass = [
      "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
      "[V4+ Styles]", "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
      "Style: Subtitle,DejaVu Sans,58,&H00FFFFFF,&H000000FF,&H00101010,&H78000000,-1,0,0,0,100,100,0,0,1,4,1,2,70,70,165,1", "",
      "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text", ...dialogueLines, "",
    ].join("\n");
    await writeFile(subtitlePath, ass, { encoding: "utf8", flag: "wx" });
    const ffmpegArgs = ["-v", "error", "-y"];
    for (const beat of normalizedBeats) {
      if (beat.visual_media_type === "image") {
        ffmpegArgs.push("-framerate", "30", "-i", beat.visual_path.absolutePath);
      } else {
        ffmpegArgs.push("-stream_loop", "-1", "-i", beat.visual_path.absolutePath);
      }
    }
    const audioInputIndex = normalizedBeats.length;
    ffmpegArgs.push("-i", audioPath.absolutePath);
    const filters = [];
    for (let index = 0; index < normalizedBeats.length; index += 1) {
      const beat = normalizedBeats[index];
      filters.push(...buildVisualBeatFilters({
        index,
        duration: beat.duration_seconds,
        isImage: beat.visual_media_type === "image",
        isFactualGraphic: beat.visual_kind === "factual_graphic",
      }));
    }
    const concatInputs = normalizedBeats.map((_, index) => `[v${index}]`).join("");
    filters.push(`${concatInputs}concat=n=${normalizedBeats.length}:v=1:a=0[vcat]`);
    filters.push(`[${audioInputIndex}:a]atrim=0:${measuredAudioDuration.toFixed(6)},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[acat]`);
    filters.push(`[vcat]subtitles=filename=${subtitlePath}:fontsdir=/usr/share/fonts/truetype/dejavu[vout]`);
    ffmpegArgs.push("-filter_complex", filters.join(";"), "-map", "[vout]", "-map", "[acat]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-shortest", temporaryOutputPath);
    execFileSync("ffmpeg", ffmpegArgs, { stdio: ["ignore", "pipe", "pipe"], maxBuffer: 64 * 1024 * 1024 });
    const probe = probeRenderedVideo(temporaryOutputPath);
    if (Math.abs(probe.duration_seconds - measuredAudioDuration) > 0.6) throw new Error(`Rendered container duration ${probe.duration_seconds} differs from voiceover ${measuredAudioDuration}`);
    if (Math.abs(probe.audio_duration_seconds - measuredAudioDuration) > 0.6) throw new Error(`Rendered audio stream duration ${probe.audio_duration_seconds} differs from voiceover ${measuredAudioDuration}`);
    if (Math.abs(probe.video_duration_seconds - measuredAudioDuration) > 0.6) throw new Error(`Rendered video stream duration ${probe.video_duration_seconds} differs from voiceover ${measuredAudioDuration}`);
    const renderedQuality = inspectRenderedVisualDiversity(temporaryOutputPath, normalizedBeats, sequenceQuality.required_unique_visual_cluster_count);
    const visualQuality = { ...sequenceQuality, ...renderedQuality, pass: true };
    const outputStat = await stat(temporaryOutputPath);
    await mkdir(renderDirectory, { recursive: true });
    await rename(temporaryOutputPath, absolutePath);
    sendJson(response, 200, {
      video_path: relativePath, media_type: "video", width: probe.width, height: probe.height, video_codec: probe.video_codec, video_pix_fmt: probe.video_pix_fmt,
      audio_codec: probe.audio_codec, audio_sample_rate: probe.audio_sample_rate, audio_channels: probe.audio_channels, duration_seconds: probe.duration_seconds,
      video_stream_duration_seconds: probe.video_duration_seconds, audio_stream_duration_seconds: probe.audio_duration_seconds,
      expected_audio_duration_seconds: measuredAudioDuration, subtitles_burned_in: true, visual_quality: visualQuality,
      beat_timings: normalizedBeats.map((beat) => ({ beat_number: beat.beat_number, start_seconds: beat.start_seconds, end_seconds: beat.end_seconds, duration_seconds: beat.duration_seconds, media_type: beat.visual_media_type, asset_key: beat.asset_key, visual_cluster_key: beat.visual_cluster_key })),
      bytes: outputStat.size,
    });
  } catch (error) {
    if (error instanceof HttpError) throw error;
    throw new HttpError(422, "render_failed", `Video could not be rendered: ${error.message}`);
  } finally {
    await rm(workDirectory, { recursive: true, force: true }).catch(() => {});
  }
}

async function serveReviewVideo(request, response, jobId) {
  const mediaPath = buildRenderPath(jobId);
  let fileStat;

  try {
    fileStat = await stat(mediaPath.absolutePath);
  } catch (error) {
    if (error?.code === "ENOENT") {
      throw new HttpError(404, "render_not_found", "Final render does not exist");
    }
    throw error;
  }

  if (!fileStat.isFile() || !Number.isSafeInteger(fileStat.size) || fileStat.size <= 0) {
    throw new HttpError(404, "render_not_found", "Final render does not exist");
  }

  let range = null;
  try {
    range = parseSingleByteRange(request.headers.range, fileStat.size);
  } catch (error) {
    if (error instanceof RangeError) {
      response.writeHead(416, {
        "Content-Range": `bytes */${fileStat.size}`,
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
      });
      response.end();
      return;
    }
    throw error;
  }

  const headers = {
    "Content-Type": "video/mp4",
    "Accept-Ranges": "bytes",
    "Cache-Control": "no-store",
  };

  if (range) {
    headers["Content-Length"] = String(range.length);
    headers["Content-Range"] = `bytes ${range.start}-${range.end}/${fileStat.size}`;
    response.writeHead(206, headers);
  } else {
    headers["Content-Length"] = String(fileStat.size);
    response.writeHead(200, headers);
  }

  if (request.method === "HEAD") {
    response.end();
    return;
  }

  const stream = range
    ? createReadStream(mediaPath.absolutePath, { start: range.start, end: range.end })
    : createReadStream(mediaPath.absolutePath);

  await new Promise((resolvePromise, rejectPromise) => {
    stream.once("error", rejectPromise);
    response.once("finish", resolvePromise);
    response.once("close", resolvePromise);
    stream.pipe(response);
  });
}

const ffmpegVersion = readToolVersion("ffmpeg");
const ffprobeVersion = readToolVersion("ffprobe");

const server = createServer(async (request, response) => {
  try {
    const requestUrl = new URL(request.url ?? "/", "http://localhost");

    if (request.method === "GET" && requestUrl.pathname === "/health") {
      sendJson(response, 200, {
        status: "ok",
        ffmpeg: ffmpegVersion,
        ffprobe: ffprobeVersion,
        semantic_ranker: {
          model: siglipModel,
          dtype: siglipDtype,
          preview_fetch_concurrency: maxConcurrentPreviewFetches,
          preview_fetch_timeout_ms: previewFetchTimeoutMs,
          preview_fetch_attempts: 1,
          preview_cache_entries: previewBufferCache.size,
          preview_cache_bytes: previewCacheBytes,
          preview_cache_max_bytes: previewCacheMaxBytes,
        },
      });
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/audio/store") {
      await storeAudio(request, response);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/audio/store-voiceover") {
      await storeContinuousVoiceover(request, response);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/audio/synthesize-free-fallback") {
      await synthesizeFreeFallbackVoiceover(request, response);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/visual/discover") {
      await discoverVisuals(request, response);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/visual/store") {
      await storeVisual(request, response, requestUrl);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/visual/store-shot") {
      await storeVisual(request, response, requestUrl, { slotParameter: "shot_number", slotPrefix: "shot" });
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/visual/contact-sheet") {
      await createVisualContactSheet(request, response);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/visual/rank") {
      await rankVisualCandidates(request, response);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/visual/inline-review-images") {
      await inlineVisualReviewImages(request, response);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/visual/fallback") {
      await createVisualFallback(request, response);
      return;
    }

    const reviewVideoMatch = /^\/review\/video\/([^/]+)$/.exec(requestUrl.pathname);
    if ((request.method === "GET" || request.method === "HEAD") && reviewVideoMatch) {
      await serveReviewVideo(request, response, reviewVideoMatch[1]);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/render-v3") {
      await renderVideoV3(request, response);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/render") {
      await renderVideo(request, response);
      return;
    }

    sendJson(response, 404, { error: "not_found" });
  } catch (error) {
    if (error instanceof HttpError) {
      sendJson(response, error.statusCode, {
        error: error.code,
        message: error.message,
      });
      return;
    }

    console.error(error);

    sendJson(response, 500, {
      error: "internal_error",
      message: "Unexpected media-worker error",
    });
  }
});

server.listen(port, "0.0.0.0", () => {
  console.log(`media-worker listening on port ${port}`);
});
