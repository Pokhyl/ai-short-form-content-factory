import http from "node:http";
import { buildOllamaRequest, callOllama, normalizeBaseUrl } from "./ollama-adapter.mjs";

const port = Number(process.env.PORT ?? 3002);
const ollamaBaseUrl = normalizeBaseUrl(process.env.OLLAMA_BASE_URL ?? "http://host.docker.internal:11434");
const textModel = String(process.env.OLLAMA_TEXT_MODEL ?? "qwen3:14b").trim();
const visionModel = String(process.env.OLLAMA_VISION_MODEL ?? "qwen3-vl:8b-instruct").trim();
const requestTimeoutMs = Math.max(10_000, Number(process.env.MODEL_REQUEST_TIMEOUT_MS ?? 150_000));
const maxBodyBytes = 20 * 1024 * 1024;

let inferenceTail = Promise.resolve();
function serializeInference(task) {
  const next = inferenceTail.then(task, task);
  inferenceTail = next.catch(() => undefined);
  return next;
}

async function readJson(request) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > maxBodyBytes) throw Object.assign(new Error("request body too large"), { statusCode: 413 });
    chunks.push(chunk);
  }
  if (!size) throw Object.assign(new Error("request body required"), { statusCode: 400 });
  try { return JSON.parse(Buffer.concat(chunks).toString("utf8")); }
  catch { throw Object.assign(new Error("invalid JSON body"), { statusCode: 400 }); }
}

function send(response, status, body) {
  response.writeHead(status, { "Content-Type": "application/json", "Cache-Control": "no-store" });
  response.end(JSON.stringify(body));
}

async function health(response) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 2500);
  try {
    const r = await fetch(`${ollamaBaseUrl}/api/tags`, { signal: controller.signal });
    const body = await r.json().catch(() => ({}));
    const available = new Set((body?.models ?? []).map((m) => String(m?.name ?? m?.model ?? "")));
    const textReady = [...available].some((name) => name === textModel || name.startsWith(`${textModel}:`));
    const visionReady = [...available].some((name) => name === visionModel || name.startsWith(`${visionModel}:`));
    const ok = r.ok && textReady && visionReady;
    send(response, ok ? 200 : 503, {
      status: ok ? "ok" : "degraded",
      provider: "ollama_self_hosted",
      base_url: ollamaBaseUrl,
      text_model: textModel,
      vision_model: visionModel,
      text_model_ready: textReady,
      vision_model_ready: visionReady,
      hosted_ai_fallback: false,
    });
  } catch (error) {
    send(response, 503, {
      status: "degraded",
      provider: "ollama_self_hosted",
      base_url: ollamaBaseUrl,
      text_model: textModel,
      vision_model: visionModel,
      text_model_ready: false,
      vision_model_ready: false,
      hosted_ai_fallback: false,
      error: String(error?.message ?? error).slice(0, 300),
    });
  } finally {
    clearTimeout(timer);
  }
}

const server = http.createServer(async (request, response) => {
  try {
    if (request.method === "GET" && request.url === "/health") return await health(response);
    if (request.method !== "POST" || request.url !== "/generate") return send(response, 404, { error: "not_found" });
    const body = await readJson(request);
    const built = buildOllamaRequest({
      prompt: body.prompt,
      input: body.input,
      temperature: body.temperature,
      textModel,
      visionModel,
    });
    const result = await serializeInference(() => callOllama({
      baseUrl: ollamaBaseUrl,
      request: built.request,
      timeoutMs: requestTimeoutMs,
    }));
    return send(response, 200, { ...result, image_count: built.imageCount });
  } catch (error) {
    const status = Number(error?.statusCode) || 502;
    return send(response, status, { error: "local_model_unavailable", detail: String(error?.message ?? error).slice(0, 600) });
  }
});

server.listen(port, "0.0.0.0", () => {
  console.log(JSON.stringify({ event: "model_worker_started", port, provider: "ollama_self_hosted", textModel, visionModel }));
});
