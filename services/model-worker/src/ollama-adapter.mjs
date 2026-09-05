const DEFAULT_TIMEOUT_MS = 300_000;

export function normalizeBaseUrl(value) {
  const raw = String(value ?? "").trim().replace(/\/+$/u, "");
  if (!raw) throw new Error("OLLAMA_BASE_URL is required");
  const parsed = new URL(raw);
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error("OLLAMA_BASE_URL must be http(s)");
  return raw;
}

export function buildOllamaRequest({ prompt, input, temperature, textModel, visionModel }) {
  const cleanPrompt = String(prompt ?? "").trim();
  const items = Array.isArray(input) ? input.filter((item) => item && typeof item === "object") : [];
  const images = [];
  const parts = [];

  if (cleanPrompt) parts.push(cleanPrompt);
  let imageIndex = 0;
  for (const item of items) {
    if (item.type === "text") {
      const text = String(item.text ?? "").trim();
      if (text) parts.push(text);
      continue;
    }
    if (item.type === "image") {
      const data = String(item.data ?? "").trim();
      if (!data) continue;
      imageIndex += 1;
      parts.push(`[IMAGE_${imageIndex}]`);
      images.push(data);
    }
  }

  const content = parts.join("\n\n").trim();
  if (!content && images.length === 0) throw new Error("prompt or multimodal input required");
  const model = images.length > 0 ? String(visionModel ?? "").trim() : String(textModel ?? "").trim();
  if (!model) throw new Error(images.length > 0 ? "OLLAMA_VISION_MODEL is required" : "OLLAMA_TEXT_MODEL is required");

  const numericTemperature = Number(temperature);
  const request = {
    model,
    messages: [{ role: "user", content, ...(images.length ? { images } : {}) }],
    stream: false,
    think: false,
    keep_alive: "5m",
    options: {
      temperature: Number.isFinite(numericTemperature) ? Math.max(0, Math.min(1, numericTemperature)) : 0.05,
      num_ctx: images.length > 0 ? 16384 : 8192,
    },
  };
  return { request, model, imageCount: images.length };
}

export async function callOllama({ baseUrl, request, timeoutMs = DEFAULT_TIMEOUT_MS, fetchImpl = fetch }) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(`${normalizeBaseUrl(baseUrl)}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: controller.signal,
    });
    const text = await response.text();
    let body = {};
    try { body = text ? JSON.parse(text) : {}; } catch { body = {}; }
    if (!response.ok) {
      const detail = String(body?.error ?? text ?? response.statusText).slice(0, 500);
      throw new Error(`Ollama HTTP ${response.status}: ${detail}`);
    }
    const content = String(body?.message?.content ?? "").trim();
    if (!content) throw new Error("Ollama returned empty assistant content");
    return {
      text: content,
      model: String(body?.model ?? request.model),
      provider: "ollama_self_hosted",
      done_reason: String(body?.done_reason ?? ""),
      total_duration_ns: Number(body?.total_duration ?? 0),
      eval_count: Number(body?.eval_count ?? 0),
    };
  } finally {
    clearTimeout(timer);
  }
}
