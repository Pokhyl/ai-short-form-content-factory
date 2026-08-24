import { execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { mkdir, rename, rm, stat, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { pipeline, env } from "@huggingface/transformers";
import { dirname, resolve, sep } from "node:path";

const port = Number(process.env.PORT ?? 3001);
const dataRoot = resolve(process.env.MEDIA_DATA_ROOT ?? "/data");
const maxJsonBodyBytes = 8 * 1024 * 1024;
const maxVisualBodyBytes = 25 * 1024 * 1024;
const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const base64Pattern = /^[A-Za-z0-9+/]+={0,2}$/;
const supportedImageTypes = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
]);
const fallbackFontPath =
  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf";
const siglipModel =
  process.env.SIGLIP_MODEL ?? "Xenova/siglip-base-patch16-224";
const siglipDtype = process.env.SIGLIP_DTYPE ?? "q4";
const siglipCacheDir = resolve(
  process.env.TRANSFORMERS_CACHE ?? `${dataRoot}/models/huggingface`,
);
const maxRankCandidates = 10;
const trustedPreviewHosts = new Set([
  "cdn.pixabay.com",
  "images.pexels.com",
  "upload.wikimedia.org",
]);

env.cacheDir = siglipCacheDir;
env.allowRemoteModels = true;

let siglipPipelinePromise = null;

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

function buildVisualPath(jobId, sceneNumber) {
  validateJobAndScene(jobId, sceneNumber);

  const fileName = `scene-${String(sceneNumber).padStart(2, "0")}.jpg`;
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

async function storeVisual(request, response, requestUrl) {
  const jobId = String(requestUrl.searchParams.get("job_id") ?? "")
    .trim()
    .toLowerCase();
  const sceneNumber = Number(requestUrl.searchParams.get("scene_number"));
  const contentType = String(request.headers["content-type"] ?? "")
    .split(";", 1)[0]
    .trim()
    .toLowerCase();

  validateJobAndScene(jobId, sceneNumber);

  if (!supportedImageTypes.has(contentType)) {
    throw new HttpError(
      415,
      "unsupported_visual_type",
      `Unsupported image Content-Type: ${contentType || "missing"}`,
    );
  }

  const visual = await readBody(request, maxVisualBodyBytes);
  const { relativePath, absolutePath } = buildVisualPath(jobId, sceneNumber);
  const directoryPath = dirname(absolutePath);
  const sourcePath = `${absolutePath}.source-${randomUUID()}`;
  const normalizedPath = `${absolutePath}.normalized-${randomUUID()}.jpg`;

  await mkdir(directoryPath, { recursive: true });

  try {
    await writeFile(sourcePath, visual, { flag: "wx" });
    const sourceProbe = probeImage(sourcePath);

    normalizeImage(sourcePath, normalizedPath);

    const normalizedProbe = probeImage(normalizedPath);
    const normalizedStat = await stat(normalizedPath);

    await rename(normalizedPath, absolutePath);
    await rm(sourcePath, { force: true });

    sendJson(response, 200, {
      visual_path: relativePath,
      media_type: "image",
      source_content_type: contentType,
      source_width: sourceProbe.width,
      source_height: sourceProbe.height,
      width: normalizedProbe.width,
      height: normalizedProbe.height,
      codec_name: normalizedProbe.codec_name,
      bytes: normalizedStat.size,
    });
  } catch (error) {
    await rm(sourcePath, { force: true }).catch(() => {});
    await rm(normalizedPath, { force: true }).catch(() => {});

    if (error instanceof HttpError) {
      throw error;
    }

    throw new HttpError(
      422,
      "invalid_visual",
      `Visual could not be stored and normalized: ${error.message}`,
    );
  }
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

    if (candidateId.length === 0 || candidateId.length > 200) {
      throw new HttpError(
        400,
        "invalid_candidate_id",
        `candidate ${index + 1} candidate_id is invalid`,
      );
    }

    return {
      candidate_id: candidateId,
      preview_url: validatePreviewUrl(candidate.preview_url),
    };
  });

  if (new Set(normalizedCandidates.map((candidate) => candidate.candidate_id)).size !== normalizedCandidates.length) {
    throw new HttpError(
      400,
      "duplicate_candidate_id",
      "candidate_id values must be unique",
    );
  }

  try {
    await mkdir(siglipCacheDir, { recursive: true });
    const classifier = await getSiglipPipeline();
    const rawOutput = await classifier(
      normalizedCandidates.map((candidate) => candidate.preview_url),
      [query],
      { hypothesis_template: "{}" },
    );

    const perImageOutput =
      normalizedCandidates.length === 1 &&
      Array.isArray(rawOutput) &&
      !Array.isArray(rawOutput[0])
        ? [rawOutput]
        : rawOutput;

    if (!Array.isArray(perImageOutput) || perImageOutput.length !== normalizedCandidates.length) {
      throw new Error("SigLIP returned an unexpected batch shape");
    }

    const ranked = normalizedCandidates
      .map((candidate, index) => {
        const score = Number(perImageOutput[index]?.[0]?.score);

        if (!Number.isFinite(score) || score < 0 || score > 1) {
          throw new Error(`SigLIP returned an invalid score for candidate ${candidate.candidate_id}`);
        }

        return { candidate_id: candidate.candidate_id, score };
      })
      .sort((left, right) => right.score - left.score)
      .map((candidate, index) => ({ ...candidate, rank: index + 1 }));

    sendJson(response, 200, {
      model: siglipModel,
      dtype: siglipDtype,
      query,
      candidate_count: ranked.length,
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

async function createVisualFallback(request, response) {
  const body = await readJsonBody(request);
  const jobId = String(body.job_id ?? "").trim().toLowerCase();
  const sceneNumber = Number(body.scene_number);
  const text = wrapFallbackText(body.text);

  const { relativePath, absolutePath } = buildVisualPath(jobId, sceneNumber);
  const directoryPath = dirname(absolutePath);
  const textPath = `${absolutePath}.text-${randomUUID()}.txt`;
  const generatedPath = `${absolutePath}.generated-${randomUUID()}.jpg`;

  await mkdir(directoryPath, { recursive: true });

  try {
    await writeFile(textPath, text, { encoding: "utf8", flag: "wx" });

    execFileSync(
      "ffmpeg",
      [
        "-v",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=0x111111:s=1080x1920:d=1",
        "-vf",
        `drawtext=fontfile=${fallbackFontPath}:textfile=${textPath}:fontcolor=white:fontsize=54:line_spacing=18:x=(w-text_w)/2:y=(h-text_h)/2`,
        "-frames:v",
        "1",
        "-q:v",
        "2",
        generatedPath,
      ],
      {
        stdio: ["ignore", "pipe", "pipe"],
      },
    );

    const probe = probeImage(generatedPath);
    const generatedStat = await stat(generatedPath);

    await rename(generatedPath, absolutePath);
    await rm(textPath, { force: true });

    sendJson(response, 200, {
      visual_path: relativePath,
      media_type: "image",
      fallback: true,
      width: probe.width,
      height: probe.height,
      codec_name: probe.codec_name,
      bytes: generatedStat.size,
    });
  } catch (error) {
    await rm(textPath, { force: true }).catch(() => {});
    await rm(generatedPath, { force: true }).catch(() => {});

    if (error instanceof HttpError) {
      throw error;
    }

    throw new HttpError(
      422,
      "fallback_generation_failed",
      `Fallback visual could not be generated: ${error.message}`,
    );
  }
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
        },
      });
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/audio/store") {
      await storeAudio(request, response);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/visual/store") {
      await storeVisual(request, response, requestUrl);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/visual/rank") {
      await rankVisualCandidates(request, response);
      return;
    }

    if (request.method === "POST" && requestUrl.pathname === "/visual/fallback") {
      await createVisualFallback(request, response);
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
