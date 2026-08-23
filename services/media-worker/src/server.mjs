import { execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { mkdir, rename, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { dirname, resolve, sep } from "node:path";

const port = Number(process.env.PORT ?? 3001);
const dataRoot = resolve(process.env.MEDIA_DATA_ROOT ?? "/data");
const maxJsonBodyBytes = 8 * 1024 * 1024;
const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const base64Pattern = /^[A-Za-z0-9+/]+={0,2}$/;

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

async function readJsonBody(request) {
  const chunks = [];
  let totalBytes = 0;

  for await (const chunk of request) {
    totalBytes += chunk.length;

    if (totalBytes > maxJsonBodyBytes) {
      throw new HttpError(
        413,
        "payload_too_large",
        `JSON body exceeds ${maxJsonBodyBytes} bytes`,
      );
    }

    chunks.push(chunk);
  }

  if (totalBytes === 0) {
    throw new HttpError(400, "empty_body", "Request body is required");
  }

  let parsed;

  try {
    parsed = JSON.parse(Buffer.concat(chunks).toString("utf8"));
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

function buildAudioPath(jobId, sceneNumber) {
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

const ffmpegVersion = readToolVersion("ffmpeg");
const ffprobeVersion = readToolVersion("ffprobe");

const server = createServer(async (request, response) => {
  try {
    if (request.method === "GET" && request.url === "/health") {
      sendJson(response, 200, {
        status: "ok",
        ffmpeg: ffmpegVersion,
        ffprobe: ffprobeVersion,
      });
      return;
    }

    if (request.method === "POST" && request.url === "/audio/store") {
      await storeAudio(request, response);
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
