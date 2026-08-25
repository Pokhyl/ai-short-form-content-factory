import { execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { mkdir, rename, rm, stat, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import sharp from "sharp";
import { pipeline, env, RawImage } from "@huggingface/transformers";
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
  "image/svg+xml",
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
  "pixabay.com",
  "images.pexels.com",
  "upload.wikimedia.org",
]);

env.cacheDir = siglipCacheDir;
env.allowRemoteModels = true;

let siglipPipelinePromise = null;
let previewFetchTail = Promise.resolve();
const previewUserAgent =
  "ai-short-form-content-factory/1.0 (https://github.com/Pokhyl/ai-short-form-content-factory)";

function sleep(milliseconds) {
  return new Promise((resolvePromise) => setTimeout(resolvePromise, milliseconds));
}

async function fetchPreviewWithRetry(url) {
  const run = async () => {
    let lastStatus = null;

    for (let attempt = 0; attempt < 4; attempt += 1) {
      const response = await fetch(url, {
        headers: { "User-Agent": previewUserAgent },
      });
      lastStatus = response.status;

      if (response.ok) {
        await sleep(50);
        return response;
      }

      if (response.status !== 429 && response.status !== 503) {
        return response;
      }

      const retryAfter = Number(response.headers.get("retry-after"));
      const delayMilliseconds = Number.isFinite(retryAfter) && retryAfter > 0
        ? Math.min(retryAfter * 1000, 5000)
        : 400 * (attempt + 1);
      await sleep(delayMilliseconds);
    }

    return { ok: false, status: lastStatus ?? 503 };
  };

  const queued = previewFetchTail.then(run, run);
  previewFetchTail = queued.then(() => undefined, () => undefined);
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
    let sourceProbe;

    if (contentType === "image/svg+xml") {
      const metadata = await sharp(visual).metadata();
      const width = Number(metadata.width);
      const height = Number(metadata.height);

      if (!Number.isInteger(width) || width <= 0 || !Number.isInteger(height) || height <= 0) {
        throw new Error("SVG metadata did not return valid dimensions");
      }

      sourceProbe = { codec_name: "svg", width, height, pix_fmt: null };
      await sharp(visual, { density: 192 })
        .flatten({ background: "#ffffff" })
        .resize({ width: 1920, height: 1920, fit: "inside", withoutEnlargement: false })
        .jpeg({ quality: 92, chromaSubsampling: "4:4:4" })
        .toFile(normalizedPath);
    } else {
      sourceProbe = probeImage(sourcePath);
      normalizeImage(sourcePath, normalizedPath);
    }

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
    const rankableCandidates = [];
    const previewImages = [];
    const rejected = [];

    for (const candidate of normalizedCandidates) {
      try {
        const previewResponse = await fetchPreviewWithRetry(candidate.preview_url);

        if (!previewResponse.ok) {
          throw new Error(`HTTP ${previewResponse.status}`);
        }

        const previewBuffer = Buffer.from(await previewResponse.arrayBuffer());
        const { data, info } = await sharp(previewBuffer)
          .flatten({ background: "#ffffff" })
          .toColourspace("srgb")
          .removeAlpha()
          .raw()
          .toBuffer({ resolveWithObject: true });

        if (info.channels !== 3) {
          throw new Error(`normalized channels=${info.channels}`);
        }

        rankableCandidates.push(candidate);
        previewImages.push(new RawImage(data, info.width, info.height, info.channels));
      } catch (error) {
        rejected.push({ candidate_id: candidate.candidate_id, reason: String(error.message ?? error).slice(0, 300) });
      }
    }

    if (rankableCandidates.length === 0) {
      throw new Error("No candidate preview could be decoded for semantic ranking");
    }

    const rawOutput = await classifier(
      previewImages,
      [query],
      { hypothesis_template: "{}" },
    );

    const perImageOutput =
      rankableCandidates.length === 1 &&
      Array.isArray(rawOutput) &&
      !Array.isArray(rawOutput[0])
        ? [rawOutput]
        : rawOutput;

    if (!Array.isArray(perImageOutput) || perImageOutput.length !== rankableCandidates.length) {
      throw new Error("SigLIP returned an unexpected batch shape");
    }

    const ranked = rankableCandidates
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
      requested_candidate_count: normalizedCandidates.length,
      rejected_candidate_count: rejected.length,
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

async function createVisualFallback(request, response) {
  const body = await readJsonBody(request);
  const jobId = String(body.job_id ?? "").trim().toLowerCase();
  const sceneNumber = Number(body.scene_number);
  const text = wrapFallbackText(body.text);
  const fallbackKind = String(body.kind ?? "text").trim().toLowerCase();

  if (!new Set(["text", "location_error"]).has(fallbackKind)) {
    throw new HttpError(
      400,
      "invalid_fallback_kind",
      "kind must be one of: text, location_error",
    );
  }

  const { relativePath, absolutePath } = buildVisualPath(jobId, sceneNumber);
  const directoryPath = dirname(absolutePath);
  const textPath = `${absolutePath}.text-${randomUUID()}.txt`;
  const generatedPath = `${absolutePath}.generated-${randomUUID()}.jpg`;

  await mkdir(directoryPath, { recursive: true });

  try {
    if (fallbackKind === "location_error") {
      const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920">
          <rect width="1080" height="1920" fill="#111318"/>
          <text x="540" y="150" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-size="58" font-weight="700" fill="#ffffff">GPS POSITION ERROR</text>
          <text x="540" y="215" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-size="32" fill="#c7ccd6">calculated position differs from actual position</text>
          <rect x="155" y="275" width="770" height="1450" rx="92" fill="#20242c" stroke="#e7eaf0" stroke-width="10"/>
          <rect x="208" y="390" width="664" height="1150" rx="30" fill="#eef1ec"/>
          <rect x="430" y="318" width="220" height="24" rx="12" fill="#6e7480"/>
          <path d="M235 540 C390 470 520 555 850 485" fill="none" stroke="#b6bdc5" stroke-width="24"/>
          <path d="M235 760 C410 700 600 735 850 660" fill="none" stroke="#c7cdd4" stroke-width="18"/>
          <path d="M270 1160 C420 1020 590 990 820 1110" fill="none" stroke="#bbc2cb" stroke-width="20"/>
          <path d="M360 410 L410 1510" fill="none" stroke="#d0d5db" stroke-width="16"/>
          <path d="M690 410 L620 1510" fill="none" stroke="#d0d5db" stroke-width="16"/>
          <circle cx="390" cy="1030" r="36" fill="#20a35a" stroke="#ffffff" stroke-width="9"/>
          <circle cx="390" cy="1030" r="78" fill="none" stroke="#20a35a" stroke-width="8" opacity="0.45"/>
          <text x="390" y="1150" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-size="34" font-weight="700" fill="#137844">ACTUAL</text>
          <path d="M710 680 C655 680 612 723 612 776 C612 850 710 972 710 972 C710 972 808 850 808 776 C808 723 765 680 710 680 Z" fill="#d9363e" stroke="#ffffff" stroke-width="8"/>
          <circle cx="710" cy="776" r="32" fill="#ffffff"/>
          <text x="710" y="1050" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-size="34" font-weight="700" fill="#bd232c">CALCULATED</text>
          <line x1="438" y1="997" x2="635" y2="850" stroke="#d9363e" stroke-width="12" stroke-dasharray="24 18"/>
          <circle cx="540" cy="925" r="48" fill="#111318" stroke="#d9363e" stroke-width="8"/>
          <text x="540" y="943" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-size="58" font-weight="700" fill="#ffffff">!</text>
          <rect x="245" y="1300" width="590" height="150" rx="28" fill="#ffffff" opacity="0.96"/>
          <text x="540" y="1365" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-size="38" font-weight="700" fill="#d9363e">WRONG LOCATION</text>
          <text x="540" y="1415" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-size="28" fill="#30343b">signal delay shifted the GPS estimate</text>
          <circle cx="540" cy="1625" r="34" fill="none" stroke="#7e8591" stroke-width="8"/>
        </svg>`;

      await sharp(Buffer.from(svg))
        .jpeg({ quality: 92, chromaSubsampling: "4:4:4" })
        .toFile(generatedPath);
    } else {
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
    }

    const probe = probeImage(generatedPath);
    const generatedStat = await stat(generatedPath);

    await rename(generatedPath, absolutePath);
    await rm(textPath, { force: true });

    sendJson(response, 200, {
      visual_path: relativePath,
      media_type: "image",
      fallback: true,
      fallback_kind: fallbackKind,
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
      "format=duration:stream=index,codec_type,codec_name,width,height,pix_fmt,sample_rate,channels",
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

  if (
    !video ||
    !audio ||
    video.codec_name !== "h264" ||
    Number(video.width) !== 1080 ||
    Number(video.height) !== 1920 ||
    audio.codec_name !== "aac" ||
    !Number.isFinite(durationSeconds) ||
    durationSeconds <= 0
  ) {
    throw new Error("ffprobe did not return the required H.264/AAC 1080x1920 output");
  }

  return {
    duration_seconds: durationSeconds,
    width: Number(video.width),
    height: Number(video.height),
    video_codec: video.codec_name,
    video_pix_fmt: video.pix_fmt ?? null,
    audio_codec: audio.codec_name,
    audio_sample_rate: Number(audio.sample_rate) || null,
    audio_channels: Number(audio.channels) || null,
  };
}

async function renderVideo(request, response) {
  const body = await readJsonBody(request);
  const jobId = String(body.job_id ?? "").trim().toLowerCase();
  const scenes = body.scenes;

  if (!uuidPattern.test(jobId)) {
    throw new HttpError(400, "invalid_job_id", "job_id must be a valid UUID");
  }

  if (!Array.isArray(scenes) || scenes.length === 0 || scenes.length > 100) {
    throw new HttpError(
      400,
      "invalid_render_scenes",
      "scenes must contain between 1 and 100 items",
    );
  }

  const normalizedScenes = [];

  for (let index = 0; index < scenes.length; index += 1) {
    const scene = scenes[index];

    if (scene === null || typeof scene !== "object" || Array.isArray(scene)) {
      throw new HttpError(
        400,
        "invalid_render_scene",
        `scene ${index + 1} must be an object`,
      );
    }

    const sceneNumber = Number(scene.scene_number);

    if (!Number.isInteger(sceneNumber) || sceneNumber !== index + 1) {
      throw new HttpError(
        400,
        "invalid_scene_number",
        `scene ${index + 1} must have sequential scene_number`,
      );
    }

    const persistedDuration = Number(scene.duration_seconds);

    if (!Number.isFinite(persistedDuration) || persistedDuration <= 0) {
      throw new HttpError(
        400,
        "invalid_scene_duration",
        `scene ${sceneNumber} duration_seconds must be positive`,
      );
    }

    const audioPath = resolvePersistedMediaPath(jobId, scene.audio_path, "audio");
    const visualPath = resolvePersistedMediaPath(jobId, scene.visual_path, "visual");
    const narration = String(scene.narration ?? "").replace(/\s+/gu, " ").trim();

    if (narration.length === 0 || narration.length > 1200) {
      throw new HttpError(
        400,
        "invalid_narration",
        `scene ${sceneNumber} narration is invalid`,
      );
    }

    let audioStat;
    let visualStat;

    try {
      [audioStat, visualStat] = await Promise.all([
        stat(audioPath.absolutePath),
        stat(visualPath.absolutePath),
      ]);
    } catch {
      throw new HttpError(
        422,
        "render_input_missing",
        `scene ${sceneNumber} media file is missing`,
      );
    }

    if (!audioStat.isFile() || !visualStat.isFile()) {
      throw new HttpError(
        422,
        "render_input_invalid",
        `scene ${sceneNumber} media input is not a file`,
      );
    }

    const measuredDuration = probeDurationSeconds(audioPath.absolutePath);

    if (Math.abs(measuredDuration - persistedDuration) > 0.15) {
      throw new HttpError(
        422,
        "audio_duration_mismatch",
        `scene ${sceneNumber} persisted duration differs from ffprobe duration`,
      );
    }

    probeImage(visualPath.absolutePath);

    normalizedScenes.push({
      scene_number: sceneNumber,
      narration,
      audio_path: audioPath,
      visual_path: visualPath,
      duration_seconds: measuredDuration,
    });
  }

  const { relativePath, absolutePath } = buildRenderPath(jobId);
  const renderDirectory = dirname(absolutePath);
  const workDirectory = `${renderDirectory}/.tmp-${randomUUID()}`;
  const subtitlePath = `${workDirectory}/subtitles.ass`;
  const temporaryOutputPath = `${workDirectory}/final.mp4`;

  await mkdir(workDirectory, { recursive: true });

  try {
    let cursor = 0;
    const dialogueLines = [];
    const timings = [];

    for (const scene of normalizedScenes) {
      const start = cursor;
      const end = cursor + scene.duration_seconds;
      timings.push({
        scene_number: scene.scene_number,
        start_seconds: start,
        end_seconds: end,
        duration_seconds: scene.duration_seconds,
      });
      dialogueLines.push(
        `Dialogue: 0,${assTime(start)},${assTime(end)},Subtitle,,0,0,0,,${escapeAssText(scene.narration)}`,
      );
      cursor = end;
    }

    const ass = [
      "[Script Info]",
      "ScriptType: v4.00+",
      "PlayResX: 1080",
      "PlayResY: 1920",
      "WrapStyle: 2",
      "ScaledBorderAndShadow: yes",
      "",
      "[V4+ Styles]",
      "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
      "Style: Subtitle,DejaVu Sans,58,&H00FFFFFF,&H000000FF,&H00101010,&H78000000,-1,0,0,0,100,100,0,0,1,4,1,2,70,70,165,1",
      "",
      "[Events]",
      "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
      ...dialogueLines,
      "",
    ].join("\n");

    await writeFile(subtitlePath, ass, { encoding: "utf8", flag: "wx" });

    const ffmpegArgs = ["-v", "error", "-y"];

    for (const scene of normalizedScenes) {
      ffmpegArgs.push(
        "-loop",
        "1",
        "-framerate",
        "30",
        "-t",
        scene.duration_seconds.toFixed(6),
        "-i",
        scene.visual_path.absolutePath,
        "-i",
        scene.audio_path.absolutePath,
      );
    }

    const filters = [];

    for (let index = 0; index < normalizedScenes.length; index += 1) {
      const duration = normalizedScenes[index].duration_seconds.toFixed(6);
      filters.push(
        `[${index * 2}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30,format=yuv420p[v${index}]`,
      );
      filters.push(
        `[${index * 2 + 1}:a]atrim=0:${duration},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a${index}]`,
      );
    }

    const concatInputs = normalizedScenes
      .map((_, index) => `[v${index}][a${index}]`)
      .join("");

    filters.push(
      `${concatInputs}concat=n=${normalizedScenes.length}:v=1:a=1[vcat][acat]`,
    );
    filters.push(
      `[vcat]subtitles=filename=${subtitlePath}:fontsdir=/usr/share/fonts/truetype/dejavu[vout]`,
    );

    ffmpegArgs.push(
      "-filter_complex",
      filters.join(";"),
      "-map",
      "[vout]",
      "-map",
      "[acat]",
      "-c:v",
      "libx264",
      "-preset",
      "medium",
      "-crf",
      "20",
      "-profile:v",
      "high",
      "-level",
      "4.1",
      "-pix_fmt",
      "yuv420p",
      "-c:a",
      "aac",
      "-b:a",
      "192k",
      "-ar",
      "48000",
      "-ac",
      "2",
      "-movflags",
      "+faststart",
      "-shortest",
      temporaryOutputPath,
    );

    execFileSync("ffmpeg", ffmpegArgs, {
      stdio: ["ignore", "pipe", "pipe"],
      maxBuffer: 32 * 1024 * 1024,
    });

    const probe = probeRenderedVideo(temporaryOutputPath);
    const expectedDuration = normalizedScenes.reduce(
      (sum, scene) => sum + scene.duration_seconds,
      0,
    );

    if (Math.abs(probe.duration_seconds - expectedDuration) > 0.6) {
      throw new Error(
        `Rendered duration ${probe.duration_seconds} differs from scene audio total ${expectedDuration}`,
      );
    }

    const outputStat = await stat(temporaryOutputPath);

    await mkdir(renderDirectory, { recursive: true });
    await rename(temporaryOutputPath, absolutePath);

    sendJson(response, 200, {
      video_path: relativePath,
      media_type: "video",
      width: probe.width,
      height: probe.height,
      video_codec: probe.video_codec,
      video_pix_fmt: probe.video_pix_fmt,
      audio_codec: probe.audio_codec,
      audio_sample_rate: probe.audio_sample_rate,
      audio_channels: probe.audio_channels,
      duration_seconds: probe.duration_seconds,
      expected_audio_duration_seconds: expectedDuration,
      subtitles_burned_in: true,
      scene_timings: timings,
      bytes: outputStat.size,
    });
  } catch (error) {
    if (error instanceof HttpError) {
      throw error;
    }

    throw new HttpError(
      422,
      "render_failed",
      `Video could not be rendered: ${error.message}`,
    );
  } finally {
    await rm(workDirectory, { recursive: true, force: true }).catch(() => {});
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
