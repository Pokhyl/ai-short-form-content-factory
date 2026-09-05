import { buildVisualSegments } from "./visual-segmentation.mjs";

const USER_AGENT = "ai-short-form-content-factory/1.0 (https://github.com/Pokhyl/ai-short-form-content-factory)";
const MAX_RESULTS_PER_PROVIDER = 18;
const FETCH_TIMEOUT_MS = 15000;
const CACHE_TTL_MS = 15 * 60 * 1000;
const CACHE_MAX_ENTRIES = 96;
const PROVIDER_QUERY_MAX_CHARS = 90;
const SEGMENT_SEARCH_CONCURRENCY = 4;
const cache = new Map();

function cleanText(value) {
  return String(value ?? "")
    .normalize("NFKC")
    .replace(/<[^>]*>/gu, " ")
    .replace(/\s+/gu, " ")
    .trim();
}

function cleanDescription(value) {
  return cleanText(value).slice(0, 1200);
}

function boundedProviderQuery(value, maxChars = PROVIDER_QUERY_MAX_CHARS) {
  const text = cleanText(value);
  if (!text || text.length <= maxChars) return text;
  const words = text.split(/\s+/u).filter(Boolean);
  let out = "";
  for (const word of words) {
    const next = out ? `${out} ${word}` : word;
    if (next.length > maxChars) break;
    out = next;
  }
  return out || text.slice(0, maxChars).trim();
}

async function mapWithConcurrency(items, limit, worker) {
  const rows = new Array(items.length);
  let cursor = 0;
  async function run() {
    while (true) {
      const index = cursor;
      cursor += 1;
      if (index >= items.length) return;
      rows[index] = await worker(items[index], index);
    }
  }
  const count = Math.max(1, Math.min(Number(limit) || 1, items.length || 1));
  await Promise.all(Array.from({ length: count }, () => run()));
  return rows;
}


function buildBeatAlignedVisualSegmentation(timedBeats) {
  const validated = buildVisualSegments(timedBeats);
  const segments = timedBeats.map((beat, index) => {
    const sceneNumber = Number(beat?.scene_number ?? beat?.beat_number);
    const start = Number(beat?.beat_start_seconds ?? beat?.start_seconds);
    const end = Number(beat?.beat_end_seconds ?? beat?.end_seconds);
    const duration = Number(beat?.duration_seconds);
    const narration = cleanText(beat?.narration);
    const support = [...new Set((Array.isArray(beat?.narration_support_evidence_ids) ? beat.narration_support_evidence_ids : beat?.support_evidence_ids ?? []).map(cleanText).filter(Boolean))];
    return {
      segment_number: index + 1,
      first_scene_number: sceneNumber,
      last_scene_number: sceneNumber,
      start_seconds: Number(start.toFixed(6)),
      end_seconds: Number(end.toFixed(6)),
      duration_seconds: Number(duration.toFixed(6)),
      narration,
      support_evidence_ids: support,
      search_terms: [],
      planned_shot_count: duration >= 1.8 ? 2 : 1,
    };
  });
  return {
    version: "narration-beat-visual-segments-v4",
    source_validation_version: validated.version,
    duration_seconds: validated.duration_seconds,
    segment_count: segments.length,
    segments,
  };
}

function mediaKindFromWikimedia(title, mime, description) {
  const lower = `${cleanText(title)} ${cleanText(description)}`.toLowerCase();
  const extension = cleanText(title).toLowerCase().match(/\.([a-z0-9]+)$/u)?.[1] ?? "";
  if (extension === "gif" || /\b(?:animation|animated)\b/u.test(lower)) return "animation";
  if (mime === "image/svg+xml" || /\b(?:diagram|schematic|drawing|chart|graph|scheme)\w*\b/u.test(lower)) return "diagram";
  return "photo";
}

function cacheGet(key) {
  const entry = cache.get(key);
  if (!entry) return null;
  if (Date.now() - entry.at > CACHE_TTL_MS) {
    cache.delete(key);
    return null;
  }
  cache.delete(key);
  cache.set(key, entry);
  return entry.value;
}

function cacheSet(key, value) {
  cache.set(key, { at: Date.now(), value });
  while (cache.size > CACHE_MAX_ENTRIES) cache.delete(cache.keys().next().value);
}

async function fetchJson(url, { headers = {}, fetchImpl = fetch } = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const response = await fetchImpl(url, {
      headers: { "User-Agent": USER_AGENT, ...headers },
      signal: controller.signal,
    });
    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}`);
      error.status = response.status;
      throw error;
    }
    return await response.json();
  } finally {
    clearTimeout(timeout);
  }
}

function normalizeWikimediaPages(pages, retrievalSource, providerQuery) {
  const supported = new Set(["image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"]);
  const result = [];
  for (const page of Array.isArray(pages) ? pages : []) {
    const info = page?.imageinfo?.[0] ?? {};
    const mime = cleanText(info.mime).toLowerCase();
    const width = Number(info.width ?? 0);
    const height = Number(info.height ?? 0);
    const downloadUrl = cleanText(info.url);
    const previewUrl = cleanText(info.thumburl ?? info.url);
    if (!supported.has(mime) || !downloadUrl || !previewUrl || width < 100 || height < 100) continue;
    const ext = info.extmetadata ?? {};
    const title = cleanText(page?.title);
    if (!title) continue;
    const description = cleanDescription(ext?.ImageDescription?.value ?? ext?.ObjectName?.value ?? "");
    const categories = cleanDescription(ext?.Categories?.value ?? "");
    const mediaKind = mediaKindFromWikimedia(title, mime, `${description} ${categories}`);
    result.push({
      candidate_id: `wikimedia:${title}`,
      provider: "wikimedia",
      provider_asset_id: title,
      media_kind: mediaKind,
      preview_urls: [previewUrl],
      preview_url: previewUrl,
      download_url: downloadUrl,
      source_url: cleanText(info.descriptionurl) || `https://commons.wikimedia.org/wiki/${encodeURIComponent(title.replace(/\s+/gu, "_"))}`,
      author: cleanDescription(ext?.Artist?.value ?? ext?.Credit?.value ?? "") || null,
      license: cleanText(ext?.LicenseShortName?.value) || null,
      license_url: cleanText(ext?.LicenseUrl?.value) || null,
      title,
      description,
      categories,
      metadata: {
        retrieval_source: retrievalSource,
        provider_query: providerQuery,
        source_title: title,
        source_description: description || null,
        source_tags: categories || null,
        source_mime: mime,
        source_width: width,
        source_height: height,
        media_type: mediaKind === "animation" ? "animation" : "image",
      },
    });
  }
  return result;
}

async function fetchCanonicalMedia({ language, title, fetchImpl }) {
  const key = `canonical:${language}:${title}`;
  const cached = cacheGet(key);
  if (cached) return cached;
  const params = new URLSearchParams({
    action: "query",
    format: "json",
    formatversion: "2",
    redirects: "1",
    titles: title,
    generator: "images",
    gimlimit: "50",
    prop: "imageinfo",
    iiprop: "url|mime|size|extmetadata",
    iiurlwidth: "640",
  });
  const data = await fetchJson(`https://${language}.wikipedia.org/w/api.php?${params}`, { fetchImpl });
  const value = normalizeWikimediaPages(data?.query?.pages ?? [], "canonical_article", title);
  cacheSet(key, value);
  return value;
}

async function fetchEnglishCanonicalTitle({ language, title, fetchImpl }) {
  if (language === "en") return title;
  const key = `langlink:${language}:${title}`;
  const cached = cacheGet(key);
  if (cached) return cached;
  const params = new URLSearchParams({
    action: "query",
    format: "json",
    formatversion: "2",
    redirects: "1",
    titles: title,
    prop: "langlinks",
    lllang: "en",
    lllimit: "1",
  });
  const data = await fetchJson(`https://${language}.wikipedia.org/w/api.php?${params}`, { fetchImpl });
  const page = (data?.query?.pages ?? [])[0] ?? {};
  const value = cleanText(page?.langlinks?.[0]?.title) || title;
  cacheSet(key, value);
  return value;
}

async function fetchCommonsSearch({ query, fetchImpl }) {
  const key = `commons:${query}`;
  const cached = cacheGet(key);
  if (cached) return cached;
  const params = new URLSearchParams({
    action: "query",
    format: "json",
    formatversion: "2",
    generator: "search",
    gsrnamespace: "6",
    gsrlimit: String(MAX_RESULTS_PER_PROVIDER),
    gsrsearch: query,
    prop: "imageinfo",
    iiprop: "url|mime|size|extmetadata",
    iiurlwidth: "640",
  });
  const data = await fetchJson(`https://commons.wikimedia.org/w/api.php?${params}`, { fetchImpl });
  const value = normalizeWikimediaPages(data?.query?.pages ?? [], "commons_search", query);
  cacheSet(key, value);
  return value;
}

async function fetchPixabay({ query, apiKey, fetchImpl }) {
  if (!apiKey) return [];
  const key = `pixabay:${query}`;
  const cached = cacheGet(key);
  if (cached) return cached;
  const params = new URLSearchParams({
    key: apiKey,
    q: query,
    image_type: "photo",
    safesearch: "true",
    per_page: String(MAX_RESULTS_PER_PROVIDER),
  });
  const data = await fetchJson(`https://pixabay.com/api/?${params}`, { fetchImpl });
  const value = [];
  for (const hit of Array.isArray(data?.hits) ? data.hits : []) {
    const id = cleanText(hit?.id);
    const downloadUrl = cleanText(hit?.largeImageURL ?? hit?.webformatURL);
    const previewUrl = cleanText(hit?.webformatURL ?? hit?.previewURL);
    const width = Number(hit?.imageWidth ?? 0), height = Number(hit?.imageHeight ?? 0);
    if (!id || !downloadUrl || !previewUrl || width < 320 || height < 320) continue;
    const tags = cleanText(hit?.tags);
    value.push({
      candidate_id: `pixabay:${id}`,
      provider: "pixabay",
      provider_asset_id: id,
      media_kind: "photo",
      preview_urls: [previewUrl],
      preview_url: previewUrl,
      download_url: downloadUrl,
      source_url: cleanText(hit?.pageURL) || null,
      author: cleanText(hit?.user) || null,
      license: "Pixabay Content License",
      license_url: "https://pixabay.com/service/license-summary/",
      title: tags || `Pixabay ${id}`,
      description: tags,
      categories: tags,
      metadata: {
        retrieval_source: "pixabay_search",
        provider_query: query,
        source_title: tags || null,
        source_description: tags || null,
        source_tags: tags || null,
        source_width: width,
        source_height: height,
        media_type: "image",
      },
    });
  }
  cacheSet(key, value);
  return value;
}

function pexelsSlug(url) {
  try {
    const path = new URL(url).pathname.split("/").filter(Boolean);
    return cleanText(path[path.length - 1]?.replace(/-\d+$/u, "").replace(/-/gu, " "));
  } catch {
    return "";
  }
}

async function fetchPexels({ query, apiKey, fetchImpl }) {
  if (!apiKey) return [];
  const key = `pexels:${query}`;
  const cached = cacheGet(key);
  if (cached) return cached;
  const params = new URLSearchParams({ query, per_page: String(Math.min(15, MAX_RESULTS_PER_PROVIDER)) });
  const data = await fetchJson(`https://api.pexels.com/v1/search?${params}`, {
    headers: { Authorization: apiKey },
    fetchImpl,
  });
  const value = [];
  for (const photo of Array.isArray(data?.photos) ? data.photos : []) {
    const id = cleanText(photo?.id);
    const width = Number(photo?.width ?? 0), height = Number(photo?.height ?? 0);
    const downloadUrl = cleanText(photo?.src?.large2x ?? photo?.src?.large ?? photo?.src?.original);
    const previewUrl = cleanText(photo?.src?.medium ?? photo?.src?.large ?? photo?.src?.large2x);
    if (!id || !downloadUrl || !previewUrl || width < 320 || height < 320) continue;
    const sourceUrl = cleanText(photo?.url);
    const description = cleanText(photo?.alt) || pexelsSlug(sourceUrl);
    value.push({
      candidate_id: `pexels:${id}`,
      provider: "pexels",
      provider_asset_id: id,
      media_kind: "photo",
      preview_urls: [previewUrl],
      preview_url: previewUrl,
      download_url: downloadUrl,
      source_url: sourceUrl || null,
      author: cleanText(photo?.photographer) || null,
      license: "Pexels License",
      license_url: "https://www.pexels.com/license/",
      title: description || `Pexels ${id}`,
      description,
      categories: description,
      metadata: {
        retrieval_source: "pexels_search",
        provider_query: query,
        source_title: description || null,
        source_description: description || null,
        source_tags: description || null,
        source_width: width,
        source_height: height,
        media_type: "image",
      },
    });
  }
  cacheSet(key, value);
  return value;
}

function dedupeCandidates(candidates) {
  const result = [];
  const seen = new Set();
  for (const candidate of candidates) {
    const key = cleanText(candidate?.candidate_id);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    result.push(candidate);
  }
  return result;
}

export async function discoverVisualCandidates({ canonicalSource, beats, timedBeats, visualQueriesEn = [], pixabayApiKey = "", pexelsApiKey = "", fetchImpl = fetch }) {
  const language = cleanText(canonicalSource?.language).toLowerCase();
  const title = cleanText(canonicalSource?.title);
  if (!/^(?:en|pl|ru|uk)$/u.test(language) || !title) throw new Error("visual discovery requires canonical source language/title");

  const segmentedMode = Array.isArray(timedBeats) && timedBeats.length > 0;
  const legacyMode = !segmentedMode && Array.isArray(beats) && beats.length > 0;
  if (!segmentedMode && !legacyMode) throw new Error("visual discovery requires timed_beats or beats");
  if (segmentedMode && timedBeats.length > 100) throw new Error("visual discovery timed_beats exceeds 100 items");
  if (legacyMode && beats.length > 100) throw new Error("visual discovery beats exceeds 100 items");

  const segmentation = segmentedMode ? buildBeatAlignedVisualSegmentation(timedBeats) : null;
  const groundedQueries = Array.isArray(visualQueriesEn)
    ? visualQueriesEn.map(cleanText).filter(Boolean).slice(0, 18)
    : [];
  if (segmentedMode && groundedQueries.length < timedBeats.length) throw new Error("visual discovery requires one ordered English query per narration beat");
  const searchUnits = segmentedMode
    ? segmentation.segments.map((segment) => ({
        unit_number: Number(segment.segment_number),
        visual_target: groundedQueries[Math.max(0, Number(segment.segment_number) - 1)],
        narration: cleanText(segment.narration),
      }))
    : beats.map((beat) => ({
        unit_number: Number(beat?.scene_number),
        visual_target: cleanText(beat?.visual_target),
        narration: cleanText(beat?.narration),
      }));

  const providerErrors = [];
  let englishTitle = title;
  let canonicalMedia = [];
  if (legacyMode) {
    const [titleResult, canonicalResult] = await Promise.allSettled([
      fetchEnglishCanonicalTitle({ language, title, fetchImpl }),
      fetchCanonicalMedia({ language, title, fetchImpl }),
    ]);
    if (titleResult.status === "fulfilled") englishTitle = titleResult.value;
    else providerErrors.push({ provider: "wikipedia_langlinks", query: title, status: Number(titleResult.reason?.status) || null, message: cleanText(titleResult.reason?.message).slice(0, 240) });
    if (canonicalResult.status === "fulfilled") canonicalMedia = canonicalResult.value;
    else providerErrors.push({ provider: "canonical_article", query: title, status: Number(canonicalResult.reason?.status) || null, message: cleanText(canonicalResult.reason?.message).slice(0, 240) });
  }

  const stockQuery = boundedProviderQuery(englishTitle || title);
  let baseCommons = [], basePixabay = [], basePexels = [];

  // Legacy non-timed callers keep a bounded topic-level inventory. The production
  // timed path deliberately does not mix topic-level stock into beat-specific pools.
  if (legacyMode) {
    const baseSpecs = [
      ["wikimedia_commons", () => fetchCommonsSearch({ query: stockQuery, fetchImpl })],
      ["pixabay", () => fetchPixabay({ query: stockQuery, apiKey: pixabayApiKey, fetchImpl })],
      ["pexels", () => fetchPexels({ query: stockQuery, apiKey: pexelsApiKey, fetchImpl })],
    ];
    const settled = await Promise.allSettled(baseSpecs.map(([, load]) => load()));
    for (let i = 0; i < baseSpecs.length; i += 1) {
      const [provider] = baseSpecs[i], result = settled[i];
      if (result.status === "fulfilled") {
        if (provider === "wikimedia_commons") baseCommons = result.value;
        if (provider === "pixabay") basePixabay = result.value;
        if (provider === "pexels") basePexels = result.value;
      } else {
        providerErrors.push({ provider, query: stockQuery, unit_number: null, status: Number(result.reason?.status) || null, message: cleanText(result.reason?.message).slice(0, 240) });
      }
    }
  }

  const unitResults = await mapWithConcurrency(searchUnits, segmentedMode ? SEGMENT_SEARCH_CONCURRENCY : 1, async (unit) => {
    const unitNumber = Number(unit.unit_number);
    const anchor = cleanText(unit.visual_target);
    const exactQuery = boundedProviderQuery(anchor || stockQuery);
    const localErrors = [];

    if (segmentedMode) {
      const specs = [
        ["wikimedia_commons", () => fetchCommonsSearch({ query: exactQuery, fetchImpl })],
        ["pixabay", () => fetchPixabay({ query: exactQuery, apiKey: pixabayApiKey, fetchImpl })],
        ["pexels", () => fetchPexels({ query: exactQuery, apiKey: pexelsApiKey, fetchImpl })],
      ];
      const settled = await Promise.allSettled(specs.map(([, load]) => load()));
      let specificCommons = [], specificPixabay = [], specificPexels = [];
      for (let i = 0; i < specs.length; i += 1) {
        const [provider] = specs[i], result = settled[i];
        if (result.status === "fulfilled") {
          if (provider === "wikimedia_commons") specificCommons = result.value;
          if (provider === "pixabay") specificPixabay = result.value;
          if (provider === "pexels") specificPexels = result.value;
        } else {
          localErrors.push({ provider, query: exactQuery, unit_number: unitNumber, status: Number(result.reason?.status) || null, message: cleanText(result.reason?.message).slice(0, 240) });
        }
      }
      // Exact beat-specific results are authoritative. Canonical article media may
      // still provide a licensed exact reference, but generic topic-level stock is
      // intentionally excluded from timed segments.
      const candidates = dedupeCandidates([
        ...specificCommons,
        ...specificPexels,
        ...specificPixabay,
      ]);
      return { unit_number: unitNumber, visual_target: anchor, candidates, provider_query: exactQuery, errors: localErrors };
    }

    let specificCommons = [];
    if (anchor && exactQuery.toLocaleLowerCase() !== stockQuery.toLocaleLowerCase()) {
      try {
        specificCommons = await fetchCommonsSearch({ query: exactQuery, fetchImpl });
      } catch (error) {
        localErrors.push({ provider: "wikimedia_commons", query: exactQuery, unit_number: unitNumber, status: Number(error?.status) || null, message: cleanText(error?.message).slice(0, 240) });
      }
    }
    const candidates = dedupeCandidates([
      ...specificCommons,
      ...canonicalMedia,
      ...baseCommons,
      ...basePexels,
      ...basePixabay,
    ]);
    return { unit_number: unitNumber, visual_target: anchor, candidates, provider_query: exactQuery || stockQuery, errors: localErrors };
  });

  for (const row of unitResults) providerErrors.push(...row.errors);

  const common = {
    canonical_source: { language, title, english_title: englishTitle || title },
    provider_errors: providerErrors,
    provider_counts: {
      canonical_article: canonicalMedia.length,
      pexels_base: basePexels.length,
      pixabay_base: basePixabay.length,
      commons_base: baseCommons.length,
      segment_query_count: segmentedMode ? unitResults.length : 0,
    },
  };

  if (segmentedMode) {
    const byNumber = new Map(unitResults.map((row) => [row.unit_number, row]));
    return {
      ...common,
      segmentation_version: segmentation.version,
      duration_seconds: segmentation.duration_seconds,
      visual_segments: segmentation.segments.map((segment) => ({
        ...segment,
        search_terms: [byNumber.get(Number(segment.segment_number))?.visual_target].filter(Boolean),
        candidates: byNumber.get(Number(segment.segment_number))?.candidates ?? [],
        provider_query: byNumber.get(Number(segment.segment_number))?.provider_query ?? stockQuery,
      })),
    };
  }

  return {
    ...common,
    beats: unitResults.map((row) => ({ scene_number: row.unit_number, candidates: row.candidates })),
  };
}
