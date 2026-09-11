import { buildVisualSegments, plannedShotCountForDuration } from "./visual-segmentation.mjs";

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


const QUERY_FILLER_WORDS = new Set([
  "a", "an", "the", "and", "or", "of", "to", "in", "on", "at", "by", "for", "from", "with", "into", "over", "under", "during", "beside", "alongside", "near", "next", "its", "their", "his", "her", "this", "that", "these", "those",
  "show", "shows", "showing", "visible", "view", "close", "up", "detailed", "detail", "inside", "outside", "modern", "historical", "real", "actual", "being",
  "image", "picture", "scene", "background", "foreground", "look", "looking", "working",
]);
const QUERY_MEDIA_CUES = new Set(["portrait", "photo", "photograph", "photography", "painting", "diagram", "schematic", "map", "micrograph", "illustration", "cutaway", "model"]);
const QUERY_LOW_SIGNAL_WORDS = new Set([
  "early", "late", "century", "scientific", "science", "research", "concept", "setting", "equipment", "laboratory", "lab",
  "experiment", "experimental", "setup", "context", "generic", "general", "representation", "representing", "technical", "structure", "internal", "external", "system", "design", "mechanism", "operation",
]);
const QUERY_RECOVERY_STYLE_WORDS = new Set(["motion", "blur", "macro", "traditional", "stylized", "dramatic"]);
const QUERY_RECOVERY_ACTION_WORDS = new Set([
  "release", "releases", "released", "releasing", "push", "pushes", "pushed", "pushing", "swing", "swings", "swinging",
  "move", "moves", "moved", "moving", "movement", "rotate", "rotates", "rotated", "rotating", "turn", "turns", "turned", "turning",
  "flow", "flows", "flowed", "flowing", "tow", "tows", "towed", "towing", "guide", "guides", "guided", "guiding",
]);

function queryWordRows(value) {
  return cleanText(value).match(/[\p{L}\p{N}]+/gu)?.map((word) => ({ raw: word, key: word.toLocaleLowerCase() })) ?? [];
}

function semanticQueryRows(value) {
  return queryWordRows(value).filter((row) => row.key.length >= 3 && !QUERY_FILLER_WORDS.has(row.key));
}

function anchorQueryRows(value) {
  return semanticQueryRows(value).filter((row) =>
    !QUERY_MEDIA_CUES.has(row.key)
    && !QUERY_LOW_SIGNAL_WORDS.has(row.key)
    && !/^\d+(?:st|nd|rd|th)$/u.test(row.key),
  );
}

function canonicalOverlapRows(query, canonicalTitle) {
  const canonical = new Set(anchorQueryRows(canonicalTitle).map((row) => row.key));
  const seen = new Set();
  return anchorQueryRows(query).filter((row) => canonical.has(row.key) && !seen.has(row.key) && seen.add(row.key));
}

function queryAnchorKeys(query, canonicalTitle) {
  const shared = canonicalOverlapRows(query, canonicalTitle);
  if (shared.length >= 2) return { keys: shared.map((row) => row.key), requireAll: true };
  const semantic = anchorQueryRows(query);
  return { keys: [...new Set(semantic.map((row) => row.key))].slice(0, 8), requireAll: false };
}

function candidateSearchText(candidate) {
  return cleanText([
    candidate?.title,
    candidate?.description,
    candidate?.categories,
    candidate?.metadata?.source_title,
    candidate?.metadata?.source_description,
    candidate?.metadata?.source_tags,
    candidate?.source_url,
  ].filter(Boolean).join(" ")).toLocaleLowerCase();
}

// Ranking must prefer what concise asset metadata says the image is, not a long
// contextual page/book description that may mention many objects absent from the pixels.
function candidateRankingText(candidate) {
  const concise = (value) => {
    const text = cleanText(value);
    return text && text.length <= 240 ? text : "";
  };
  return cleanText([
    candidate?.title,
    concise(candidate?.description),
    candidate?.categories,
    candidate?.metadata?.source_title,
    concise(candidate?.metadata?.source_description),
    candidate?.metadata?.source_tags,
    candidate?.source_url,
  ].filter(Boolean).join(" ")).toLocaleLowerCase();
}

function relatedAnchorKey(left, right) {
  if (left === right) return true;
  const singular = (value) => value.length >= 5 && value.endsWith("s") ? value.slice(0, -1) : value;
  const a = singular(left), b = singular(right);
  if (a === b) return true;
  if (a.length < 5 || b.length < 5) return false;
  return a.slice(0, 6) === b.slice(0, 6);
}

function candidateQueryAnchorMetrics(candidate, query, canonicalTitle) {
  const anchor = queryAnchorKeys(query, canonicalTitle);
  const words = [...new Set(queryWordRows(candidateSearchText(candidate)).map((row) => row.key))];
  const hits = anchor.keys.filter((key) => words.some((word) => relatedAnchorKey(key, word))).length;
  const required = anchor.requireAll ? anchor.keys.length : (anchor.keys.length <= 1 ? anchor.keys.length : Math.min(anchor.keys.length >= 4 ? 3 : 2, anchor.keys.length));
  return {
    keys: anchor.keys,
    hits,
    required,
    pass: required > 0 && hits >= required,
    require_all: anchor.requireAll,
  };
}

function withCandidateAnchorMetrics(candidate, query, canonicalTitle) {
  const metrics = candidateQueryAnchorMetrics(candidate, query, canonicalTitle);
  return {
    ...candidate,
    target_anchor_keys: metrics.keys,
    target_anchor_hits: metrics.hits,
    target_anchor_required: metrics.required,
    target_anchor_pass: metrics.pass,
    target_anchor_require_all: metrics.require_all,
  };
}

function candidateMatchesQueryAnchor(candidate, query, canonicalTitle) {
  return candidateQueryAnchorMetrics(candidate, query, canonicalTitle).pass;
}

function compactRecoveryQuery(query, canonicalTitle) {
  const exact = boundedProviderQuery(query);
  const shared = canonicalOverlapRows(query, canonicalTitle);
  const mediaCue = semanticQueryRows(query).find((row) => QUERY_MEDIA_CUES.has(row.key));
  const canonicalMediaCue = mediaCue
    ? ({ schematic: "diagram", cutaway: "diagram", photograph: "photo", photography: "photo" }[mediaCue.key] ?? mediaCue.key)
    : null;
  const sharedKeys = new Set(shared.map((row) => row.key));
  const contentRows = anchorQueryRows(query).map((row, index) => ({ ...row, index }));
  const rankedContentRows = contentRows
    .filter((row) => !sharedKeys.has(row.key))
    .sort((left, right) => {
      const leftStyle = QUERY_RECOVERY_STYLE_WORDS.has(left.key) ? 1 : 0;
      const rightStyle = QUERY_RECOVERY_STYLE_WORDS.has(right.key) ? 1 : 0;
      if (leftStyle !== rightStyle) return leftStyle - rightStyle;
      const leftAction = QUERY_RECOVERY_ACTION_WORDS.has(left.key) ? 1 : 0;
      const rightAction = QUERY_RECOVERY_ACTION_WORDS.has(right.key) ? 1 : 0;
      if (leftAction !== rightAction) return leftAction - rightAction;
      const leftAcronym = /^[A-Z0-9]{2,}$/u.test(left.raw) ? 1 : 0;
      const rightAcronym = /^[A-Z0-9]{2,}$/u.test(right.raw) ? 1 : 0;
      if (leftAcronym !== rightAcronym) return rightAcronym - leftAcronym;
      if (left.raw.length !== right.raw.length) return right.raw.length - left.raw.length;
      return right.index - left.index;
    });
  const rows = [];
  const seen = new Set();
  const pushRow = (row) => {
    const key = cleanText(row?.key ?? row?.raw).toLocaleLowerCase();
    if (!key || seen.has(key)) return;
    seen.add(key);
    rows.push({ raw: cleanText(row?.raw ?? key), key });
  };
  for (const row of shared.slice(0, 2)) pushRow(row);
  const desiredContentCount = 2;
  for (const row of rankedContentRows) {
    if (rows.length >= desiredContentCount) break;
    pushRow(row);
  }
  if (canonicalMediaCue && shared.length >= 2) pushRow({ raw: canonicalMediaCue, key: canonicalMediaCue });
  const compact = boundedProviderQuery(rows.map((row) => row.raw).join(" "));
  if (!compact || compact.toLocaleLowerCase() === exact.toLocaleLowerCase()) return null;
  return compact;
}

// Inventory retrieval is budgeted before verification. A stock provider returning
// generic subject photos must not suppress a second, detail-bearing search.
function inventoryDetailQuery(query, canonicalTitle, visualTarget = "") {
  const shared = canonicalOverlapRows(query, canonicalTitle);
  const sharedKeys = new Set(shared.map((row) => row.key));
  const queryDetails = anchorQueryRows(query).filter((row) => !sharedKeys.has(row.key));
  const targetDetails = anchorQueryRows(visualTarget).filter((row) => !sharedKeys.has(row.key));
  const matched = targetDetails.filter((row) => queryDetails.some((queryRow) => relatedAnchorKey(row.key, queryRow.key)));
  const targetOnly = targetDetails.filter((row) => !queryDetails.some((queryRow) => relatedAnchorKey(row.key, queryRow.key)));
  const rankRows = (rows) => rows.map((row, index) => ({ ...row, index }))
    .sort((left, right) => {
      const leftAction = QUERY_RECOVERY_ACTION_WORDS.has(left.key) ? 1 : 0;
      const rightAction = QUERY_RECOVERY_ACTION_WORDS.has(right.key) ? 1 : 0;
      if (leftAction !== rightAction) return leftAction - rightAction;
      if (left.raw.length !== right.raw.length) return right.raw.length - left.raw.length;
      return left.index - right.index;
    });
  const ranked = [...rankRows(matched), ...rankRows(targetOnly), ...rankRows(queryDetails)].filter((row, index, rows) => rows.findIndex((other) => relatedAnchorKey(row.key, other.key)) === index);
  const mediaCue = semanticQueryRows(visualTarget || query).find((row) => QUERY_MEDIA_CUES.has(row.key));
  const canonicalMediaCue = mediaCue
    ? ({ schematic: "diagram", cutaway: "diagram", photograph: "photo", photography: "photo" }[mediaCue.key] ?? mediaCue.key)
    : null;
  if (!shared.length || (!ranked.length && !canonicalMediaCue)) return null;
  const rows = [...shared.slice(0, 2).map((row) => row.raw), ...ranked.slice(0, 2).map((row) => row.raw)];
  if (canonicalMediaCue && !rows.some((value) => relatedAnchorKey(cleanText(value).toLocaleLowerCase(), canonicalMediaCue))) rows.push(canonicalMediaCue);
  const value = boundedProviderQuery(rows.join(" "));
  return value && value.toLocaleLowerCase() !== query.toLocaleLowerCase() ? value : null;
}

function inventoryFallbackQueries(query, canonicalTitle, visualTarget = "") {
  const shared = canonicalOverlapRows(query, canonicalTitle);
  if (!shared.length) return [];
  const sharedKeys = new Set(shared.map((row) => row.key));
  const canonicalRows = anchorQueryRows(canonicalTitle);
  const canonicalComponents = canonicalRows.filter((row) => !sharedKeys.has(row.key));
  const queryDetails = anchorQueryRows(query).filter((row) => !sharedKeys.has(row.key));
  const targetDetails = anchorQueryRows(visualTarget).filter((row) => !sharedKeys.has(row.key));
  const matched = targetDetails.filter((row) => queryDetails.some((queryRow) => relatedAnchorKey(row.key, queryRow.key)));
  const targetOnly = targetDetails.filter((row) => !queryDetails.some((queryRow) => relatedAnchorKey(row.key, queryRow.key)));
  const queryOnly = queryDetails.filter((row) => !targetDetails.some((targetRow) => relatedAnchorKey(row.key, targetRow.key)));
  const rankRows = (rows) => rows.map((row, index) => ({ ...row, index }))
    .sort((left, right) => {
      const leftAction = QUERY_RECOVERY_ACTION_WORDS.has(left.key) ? 1 : 0;
      const rightAction = QUERY_RECOVERY_ACTION_WORDS.has(right.key) ? 1 : 0;
      if (leftAction !== rightAction) return leftAction - rightAction;
      if (left.raw.length !== right.raw.length) return right.raw.length - left.raw.length;
      return left.index - right.index;
    });
  const matchedRanked = rankRows(matched);
  const targetOnlyRanked = rankRows(targetOnly);
  const queryOnlyRanked = rankRows(queryOnly);
  const details = [matchedRanked[0], targetOnlyRanked[0], ...matchedRanked.slice(1), ...targetOnlyRanked.slice(1)]
    .filter(Boolean)
    .filter((row, index, rows) => rows.findIndex((other) => relatedAnchorKey(row.key, other.key)) === index);
  const subject = shared.slice(0, 2).map((row) => row.raw).join(" ");
  const component = canonicalComponents.find((row) => !details.some((detail) => relatedAnchorKey(row.key, detail.key)));
  const out = [];
  const reservedQueryDetail = matchedRanked.length < 3 ? (queryOnlyRanked.find((row) => !QUERY_RECOVERY_ACTION_WORDS.has(row.key) && !QUERY_RECOVERY_STYLE_WORDS.has(row.key) && !new Set(['cross','section']).has(row.key)) ?? null) : null;
  const ordinaryLimit = reservedQueryDetail ? 2 : 3;
  const push = (value) => {
    const bounded = boundedProviderQuery(value);
    if (!bounded || bounded.toLocaleLowerCase() === cleanText(query).toLocaleLowerCase()) return;
    if (!out.some((item) => item.toLocaleLowerCase() === bounded.toLocaleLowerCase())) out.push(bounded);
  };
  if (component) {
    const componentDetails = (matchedRanked.length ? matchedRanked : details).slice(0, 2);
    for (const row of componentDetails) {
      push(`${subject} ${component.raw} ${row.raw}`);
      if (out.length >= ordinaryLimit) break;
    }
  }
  for (const row of details) {
    if (out.length >= ordinaryLimit) break;
    push(`${subject} ${row.raw}`);
  }
  if (reservedQueryDetail && out.length < 3) push(`${subject} ${component?.raw ?? ''} ${reservedQueryDetail.raw}`);
  const mediaCue = semanticQueryRows(visualTarget).find((row) => QUERY_MEDIA_CUES.has(row.key));
  if (mediaCue && out.length < 3) {
    const cue = ({ schematic: "diagram", cutaway: "diagram", photograph: "photo", photography: "photo" }[mediaCue.key] ?? mediaCue.raw);
    push(`${subject} ${cue}`);
  }
  return out.slice(0, 3);
}

function rankInventoryCandidates(candidates, query, canonicalTitle, visualTarget = "", identityMode = "named_subject") {
  const semanticTopic = cleanText(identityMode) === "semantic_topic";
  const sharedRows = semanticTopic ? [] : canonicalOverlapRows(query, canonicalTitle);
  const shared = new Set(sharedRows.map((row) => row.key));
  const identityKeys = semanticTopic ? [] : sharedRows.slice(0, 2).map((row) => row.key);
  const details = anchorQueryRows(visualTarget || query).filter((row) => !shared.has(row.key));
  const detailRequired = Math.min(2, Math.max(1, details.length));
  const score = (candidate) => {
    const words = queryWordRows(candidateRankingText(candidate));
    const subjectHits = identityKeys.filter((key) => words.some((word) => relatedAnchorKey(key, word.key))).length;
    const detailHits = details.filter((detail) => words.some((word) => relatedAnchorKey(detail.key, word.key))).length;
    return { subjectHits, detailHits };
  };
  return candidates.map((candidate, index) => ({ candidate, index, ...score(candidate) }))
    .sort((a, b) => b.detailHits - a.detailHits || b.subjectHits - a.subjectHits || a.index - b.index)
    .map(({ candidate, subjectHits, detailHits }) => ({
      ...candidate,
      inventory_identity_mode: semanticTopic ? "semantic_topic" : "named_subject",
      inventory_subject_anchor_keys: identityKeys,
      inventory_subject_anchor_hits: subjectHits,
      inventory_subject_anchor_required: identityKeys.length,
      inventory_subject_anchor_pass: semanticTopic || identityKeys.length < 2 || subjectHits === identityKeys.length,
      inventory_detail_hits: detailHits,
      inventory_detail_required: detailRequired,
      inventory_detail_anchor_count: details.length,
    }));
}

function semanticInventoryFallbackQueries(query, visualTarget = "") {
  const out = [];
  const push = (value) => {
    const bounded = boundedProviderQuery(value);
    if (!bounded || bounded.toLocaleLowerCase() === cleanText(query).toLocaleLowerCase()) return;
    if (!out.some((item) => item.toLocaleLowerCase() === bounded.toLocaleLowerCase())) out.push(bounded);
  };
  const targetRows = anchorQueryRows(visualTarget);
  const queryRows = anchorQueryRows(query);
  if (targetRows.length) push(targetRows.slice(0, 5).map((row) => row.raw).join(" "));
  const targetKeys = new Set(targetRows.map((row) => row.key));
  const extra = queryRows.filter((row) => !targetKeys.has(row.key)).slice(0, 2);
  if (targetRows.length || extra.length) push([...targetRows.slice(0, 3), ...extra].map((row) => row.raw).join(" "));
  const mediaCue = semanticQueryRows(visualTarget).find((row) => QUERY_MEDIA_CUES.has(row.key));
  if (mediaCue) push(`${targetRows.slice(0, 3).map((row) => row.raw).join(" ")} ${{ schematic: "diagram", cutaway: "diagram", photograph: "photo", photography: "photo" }[mediaCue.key] ?? mediaCue.raw}`);
  return out.slice(0, 3);
}

function markRecoveryCandidates(candidates, recoveryQuery) {
  return candidates.map((candidate) => ({
    ...candidate,
    metadata: {
      ...(candidate.metadata ?? {}),
      retrieval_source: `${cleanText(candidate?.metadata?.retrieval_source) || candidate.provider || "provider"}_bounded_recovery`,
      provider_query: recoveryQuery,
      bounded_query_recovery: true,
    },
  }));
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
      planned_shot_count: plannedShotCountForDuration(duration),
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

async function fetchPixabay({ query, apiKey, fetchImpl, orientation = "" }) {
  if (!apiKey) return [];
  const key = `pixabay:${cleanText(orientation)}:${query}`;
  const cached = cacheGet(key);
  if (cached) return cached;
  const params = new URLSearchParams({
    key: apiKey,
    q: query,
    image_type: "photo",
    safesearch: "true",
    per_page: String(MAX_RESULTS_PER_PROVIDER),
  });
  if (cleanText(orientation) === "vertical") params.set("orientation", "vertical");
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

async function fetchPexels({ query, apiKey, fetchImpl, orientation = "" }) {
  if (!apiKey) return [];
  const key = `pexels:${cleanText(orientation)}:${query}`;
  const cached = cacheGet(key);
  if (cached) return cached;
  const params = new URLSearchParams({ query, per_page: String(Math.min(15, MAX_RESULTS_PER_PROVIDER)) });
  if (cleanText(orientation) === "portrait") params.set("orientation", "portrait");
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


export async function recoverVisualConflictCandidates({
  visualTarget,
  canonicalSubject = "",
  excludeCandidateIds = [],
  pixabayApiKey = "",
  pexelsApiKey = "",
  fetchImpl = fetch,
}) {
  const target = cleanText(visualTarget);
  if (!target) throw new Error("visual conflict recovery requires exact visual_target");
  const query = boundedProviderQuery(target);
  const excluded = new Set((Array.isArray(excludeCandidateIds) ? excludeCandidateIds : []).map(cleanText).filter(Boolean));
  const specs = [
    ["wikimedia_commons", () => fetchCommonsSearch({ query, fetchImpl })],
    ["pixabay", () => fetchPixabay({ query, apiKey: pixabayApiKey, fetchImpl })],
    ["pexels", () => fetchPexels({ query, apiKey: pexelsApiKey, fetchImpl })],
  ];
  const settled = await Promise.allSettled(specs.map(([, load]) => load()));
  const rows = [];
  const providerErrors = [];
  for (let i = 0; i < specs.length; i += 1) {
    const [provider] = specs[i], result = settled[i];
    if (result.status === "fulfilled") rows.push(...result.value);
    else providerErrors.push({
      provider,
      query,
      status: Number(result.reason?.status) || null,
      message: cleanText(result.reason?.message).slice(0, 240),
    });
  }
  const canonical = cleanText(canonicalSubject) || target;
  const deduped = dedupeCandidates(rows).filter((candidate) => !excluded.has(cleanText(candidate?.candidate_id)));
  const annotated = deduped.map((candidate) => withCandidateAnchorMetrics(candidate, target, canonical));
  const candidates = annotated.filter((candidate) => candidate.target_anchor_pass === true);
  return {
    visual_target: target,
    canonical_subject: canonical,
    provider_query: query,
    candidates,
    excluded_candidate_count: excluded.size,
    semantic_rejected_candidate_count: annotated.length - candidates.length,
    provider_errors: providerErrors,
    bounded_global_conflict_recovery: true,
  };
}

export async function discoverVisualCandidates({ canonicalSource, beats, timedBeats, inventoryClaims, explorationQueries, preclaimAssets = [], visualQueriesEn = [], pixabayApiKey = "", pexelsApiKey = "", fetchImpl = fetch }) {
  const language = cleanText(canonicalSource?.language).toLowerCase();
  const title = cleanText(canonicalSource?.title);
  if (!/^(?:en|pl|ru|uk)$/u.test(language) || !title) throw new Error("visual discovery requires canonical source language/title");

  const segmentedMode = Array.isArray(timedBeats) && timedBeats.length > 0;
  const inventoryMode = !segmentedMode && Array.isArray(inventoryClaims) && inventoryClaims.length > 0;
  const explorationMode = !segmentedMode && !inventoryMode && Array.isArray(explorationQueries) && explorationQueries.length > 0;
  const legacyMode = !segmentedMode && !inventoryMode && !explorationMode && Array.isArray(beats) && beats.length > 0;
  if (!segmentedMode && !inventoryMode && !explorationMode && !legacyMode) throw new Error("visual discovery requires timed_beats, inventory_claims, exploration_queries or beats");
  if (segmentedMode && timedBeats.length > 100) throw new Error("visual discovery timed_beats exceeds 100 items");
  if (inventoryMode && inventoryClaims.length > 30) throw new Error("visual discovery inventory_claims exceeds 30 items");
  if (explorationMode && explorationQueries.length > 30) throw new Error("visual discovery exploration_queries exceeds 30 items");
  if (legacyMode && beats.length > 100) throw new Error("visual discovery beats exceeds 100 items");

  const segmentation = segmentedMode ? buildBeatAlignedVisualSegmentation(timedBeats) : null;
  const groundedQueries = Array.isArray(visualQueriesEn)
    ? visualQueriesEn.map(cleanText).filter(Boolean).slice(0, 18)
    : [];
  if (segmentedMode && groundedQueries.length < timedBeats.length) throw new Error("visual discovery requires one ordered English query per narration beat");
  const searchUnits = inventoryMode
    ? inventoryClaims.map((claim, index) => ({
        unit_number: Number(claim?.claim_number ?? index + 1),
        visual_target: cleanText(claim?.visual_target),
        search_query: cleanText(claim?.search_query_en),
        narration: cleanText(claim?.claim),
        availability_asset_ids: Array.isArray(claim?.inventory_asset_ids) ? claim.inventory_asset_ids.map(cleanText).filter(Boolean) : [],
        required_images: 2,
      }))
    : explorationMode
      ? explorationQueries.map((query, index) => ({
          unit_number: Number(query?.query_number ?? index + 1),
          visual_target: cleanText(query?.observable_target),
          search_query: cleanText(query?.search_query_en),
          narration: cleanText(query?.retrieval_rationale ?? query?.observable_target),
          identity_mode: cleanText(query?.identity_mode) || "named_subject",
          crop_policy: cleanText(query?.crop_policy),
          required_images: 1,
        }))
    : segmentedMode
      ? segmentation.segments.map((segment) => ({
          unit_number: Number(segment.segment_number),
          visual_target: groundedQueries[Math.max(0, Number(segment.segment_number) - 1)],
          narration: cleanText(segment.narration),
          required_images: Math.max(1, Number(segment.planned_shot_count) || 1),
        }))
      : beats.map((beat) => ({
          unit_number: Number(beat?.scene_number),
          visual_target: cleanText(beat?.visual_target),
          narration: cleanText(beat?.narration),
          required_images: 1,
        }));
  if (inventoryMode && searchUnits.some((unit, index) => unit.unit_number !== index + 1 || !unit.visual_target || !unit.narration)) {
    throw new Error("visual discovery inventory_claims must be sequential complete claims");
  }
  if (explorationMode && searchUnits.some((unit, index) => unit.unit_number !== index + 1 || !unit.visual_target || !unit.search_query)) {
    throw new Error("visual discovery exploration_queries must be sequential complete queries");
  }

  const providerErrors = [];
  let englishTitle = title;
  let canonicalMedia = [];
  const [titleResult, canonicalResult] = await Promise.allSettled([
    fetchEnglishCanonicalTitle({ language, title, fetchImpl }),
    fetchCanonicalMedia({ language, title, fetchImpl }),
  ]);
  if (titleResult.status === "fulfilled") englishTitle = titleResult.value;
  else providerErrors.push({ provider: "wikipedia_langlinks", query: title, status: Number(titleResult.reason?.status) || null, message: cleanText(titleResult.reason?.message).slice(0, 240) });
  if (canonicalResult.status === "fulfilled") canonicalMedia = canonicalResult.value;
  else providerErrors.push({ provider: "canonical_article", query: title, status: Number(canonicalResult.reason?.status) || null, message: cleanText(canonicalResult.reason?.message).slice(0, 240) });

  const stockQuery = boundedProviderQuery(englishTitle || title);
  let baseCommons = [], basePixabay = [], basePexels = [];

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

  async function fetchTimedProviderSet(query, unitNumber, cropPolicy = "") {
    const specs = [
      ["wikimedia_commons", () => fetchCommonsSearch({ query, fetchImpl })],
      ["pixabay", () => fetchPixabay({ query, apiKey: pixabayApiKey, fetchImpl, orientation: cleanText(cropPolicy) === "portrait_required" ? "vertical" : "" })],
      ["pexels", () => fetchPexels({ query, apiKey: pexelsApiKey, fetchImpl, orientation: cleanText(cropPolicy) === "portrait_required" ? "portrait" : "" })],
    ];
    const settled = await Promise.allSettled(specs.map(([, load]) => load()));
    const rows = [];
    const errors = [];
    for (let i = 0; i < specs.length; i += 1) {
      const [provider] = specs[i], result = settled[i];
      if (result.status === "fulfilled") rows.push(...result.value);
      else errors.push({ provider, query, unit_number: unitNumber, status: Number(result.reason?.status) || null, message: cleanText(result.reason?.message).slice(0, 240) });
    }
    return { candidates: dedupeCandidates(rows), errors };
  }

  const unitResults = await mapWithConcurrency(searchUnits, (segmentedMode || inventoryMode || explorationMode) ? SEGMENT_SEARCH_CONCURRENCY : 1, async (unit) => {
    const unitNumber = Number(unit.unit_number);
    const anchor = cleanText(unit.visual_target);
    const exactQuery = boundedProviderQuery(unit.search_query || anchor || stockQuery);
    const localErrors = [];

    if (explorationMode) {
      const exact = await fetchTimedProviderSet(exactQuery, unitNumber, unit.crop_policy);
      localErrors.push(...exact.errors);
      const providerQueries = [exactQuery];
      let recoveryUsed = false;
      let candidates = dedupeCandidates([...canonicalMedia, ...exact.candidates]);
      const identityMode = cleanText(unit.identity_mode) || "named_subject";
      const rerank = () => rankInventoryCandidates(candidates, exactQuery, englishTitle, anchor, identityMode)
        .filter((candidate) => candidate.inventory_subject_anchor_pass === true);
      let ranked = rerank();
      const detailCount = () => ranked.filter((candidate) => Number(candidate.inventory_detail_hits) >= Number(candidate.inventory_detail_required || 1)).length;
      const recovery = (identityMode === "semantic_topic"
        ? semanticInventoryFallbackQueries(exactQuery, anchor)
        : [inventoryDetailQuery(exactQuery, englishTitle, anchor), ...inventoryFallbackQueries(exactQuery, englishTitle, anchor)])
        .filter(Boolean)
        .filter((value, index, rows) => rows.findIndex((other) => other.toLocaleLowerCase() === value.toLocaleLowerCase()) === index)
        .slice(0, 4);
      if (ranked.length < 6 || detailCount() < 2) {
        for (const recoveryQuery of recovery) {
          if (providerQueries.some((value) => value.toLocaleLowerCase() === recoveryQuery.toLocaleLowerCase())) continue;
          const recovered = await fetchTimedProviderSet(recoveryQuery, unitNumber, unit.crop_policy);
          localErrors.push(...recovered.errors);
          providerQueries.push(recoveryQuery);
          candidates = dedupeCandidates([...candidates, ...markRecoveryCandidates(recovered.candidates, recoveryQuery)]);
          recoveryUsed = true;
          ranked = rerank();
          if (ranked.length >= 6 && detailCount() >= 2) break;
        }
      }
      return {
        unit_number: unitNumber,
        visual_target: anchor,
        candidates: ranked.slice(0, 12),
        provider_query: exactQuery,
        provider_queries: providerQueries,
        bounded_query_recovery_used: recoveryUsed,
        errors: localErrors,
      };
    }

    if (segmentedMode || inventoryMode) {
      const exact = await fetchTimedProviderSet(exactQuery, unitNumber);
      localErrors.push(...exact.errors);
      const required = Math.max(1, Number(unit.required_images) || 1);
      const exactAnnotated = exact.candidates.map((candidate) => withCandidateAnchorMetrics(candidate, anchor, englishTitle));
      const exactStrong = exactAnnotated.filter((candidate) => candidate.target_anchor_pass === true);
      const canonicalAnnotated = canonicalMedia.map((candidate) => withCandidateAnchorMetrics(candidate, anchor, englishTitle));
      const canonicalExact = canonicalAnnotated.filter((candidate) => candidate.target_anchor_pass === true);
      const availabilityIds = new Set(Array.isArray(unit.availability_asset_ids) ? unit.availability_asset_ids : []);
      const seededAnnotated = inventoryMode && availabilityIds.size
        ? preclaimAssets.filter((asset) => availabilityIds.has(cleanText(asset?.inventory_id))).map((asset) => withCandidateAnchorMetrics({
            ...asset,
            description: cleanText([asset?.preclaim_visible_description, asset?.description].filter(Boolean).join(" | ")),
            metadata: { ...(asset?.metadata ?? {}), preclaim_visible_description: cleanText(asset?.preclaim_visible_description), preclaim_inventory_id: cleanText(asset?.inventory_id) },
          }, anchor, englishTitle)).filter((candidate) => candidate.target_anchor_pass === true)
        : [];
      let candidates = dedupeCandidates([...seededAnnotated, ...canonicalExact, ...exactStrong]);
      if (candidates.length < required) candidates = dedupeCandidates([...candidates, ...canonicalAnnotated]);
      const recoveryQuery = inventoryMode
        ? inventoryDetailQuery(exactQuery, englishTitle, anchor)
        : candidates.length < required ? compactRecoveryQuery(anchor, englishTitle) : null;
      const providerQueries = [exactQuery];
      let recoveryUsed = false;
      if (recoveryQuery) {
        const recovered = await fetchTimedProviderSet(recoveryQuery, unitNumber);
        localErrors.push(...recovered.errors);
        providerQueries.push(recoveryQuery);
        const recoveredStrong = recovered.candidates
          .map((candidate) => withCandidateAnchorMetrics(candidate, anchor, englishTitle))
          .filter((candidate) => candidate.target_anchor_pass === true);
        const recoveredRows = markRecoveryCandidates(recoveredStrong, recoveryQuery);
        candidates = dedupeCandidates([...candidates, ...recoveredRows]);
        recoveryUsed = true;
      }
      if (inventoryMode) {
        const desiredDetailCandidates = Math.max(2, required);
        let rankedInventory = rankInventoryCandidates(candidates, exactQuery, englishTitle, anchor);
        const detailCount = () => rankedInventory.filter((candidate) => candidate.inventory_subject_anchor_pass === true && Number(candidate.inventory_detail_hits) >= Number(candidate.inventory_detail_required || 1)).length;
        if (detailCount() < desiredDetailCandidates) {
          for (const fallbackQuery of inventoryFallbackQueries(exactQuery, englishTitle, anchor)) {
            if (providerQueries.some((value) => value.toLocaleLowerCase() === fallbackQuery.toLocaleLowerCase())) continue;
            const fallback = await fetchTimedProviderSet(fallbackQuery, unitNumber);
            localErrors.push(...fallback.errors);
            providerQueries.push(fallbackQuery);
            const fallbackStrong = fallback.candidates
              .map((candidate) => withCandidateAnchorMetrics(candidate, anchor, englishTitle))
              .filter((candidate) => candidate.target_anchor_pass === true);
            candidates = dedupeCandidates([...candidates, ...markRecoveryCandidates(fallbackStrong, fallbackQuery)]);
            recoveryUsed = true;
            rankedInventory = rankInventoryCandidates(candidates, exactQuery, englishTitle, anchor);
            if (detailCount() >= desiredDetailCandidates) break;
          }
        }
        candidates = rankedInventory;
      }
      return {
        unit_number: unitNumber,
        visual_target: anchor,
        candidates: inventoryMode ? candidates : candidates,
        provider_query: exactQuery,
        provider_queries: providerQueries,
        bounded_query_recovery_used: recoveryUsed,
        errors: localErrors,
      };
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
    return { unit_number: unitNumber, visual_target: anchor, candidates, provider_query: exactQuery || stockQuery, provider_queries: [exactQuery || stockQuery], bounded_query_recovery_used: false, errors: localErrors };
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
      inventory_query_count: inventoryMode ? unitResults.length : 0,
      exploration_query_count: explorationMode ? unitResults.length : 0,
      segment_recovery_query_count: segmentedMode ? unitResults.filter((row) => row.bounded_query_recovery_used).length : 0,
      inventory_recovery_query_count: inventoryMode ? unitResults.filter((row) => row.bounded_query_recovery_used).length : 0,
      exploration_recovery_query_count: explorationMode ? unitResults.filter((row) => row.bounded_query_recovery_used).length : 0,
    },
  };


  if (explorationMode) {
    const byNumber = new Map(unitResults.map((row) => [row.unit_number, row]));
    return {
      ...common,
      exploration_version: "pre-claim-visual-exploration-v1",
      exploration_queries: explorationQueries.map((query, index) => {
        const number = index + 1;
        const row = byNumber.get(number);
        return {
          ...query,
          query_number: number,
          candidates: row?.candidates ?? [],
          provider_query: row?.provider_query ?? cleanText(query?.search_query_en),
          provider_queries: row?.provider_queries ?? [cleanText(query?.search_query_en)].filter(Boolean),
          bounded_query_recovery_used: row?.bounded_query_recovery_used === true,
        };
      }),
    };
  }

  if (inventoryMode) {
    const byNumber = new Map(unitResults.map((row) => [row.unit_number, row]));
    return {
      ...common,
      inventory_version: "pre-script-visual-inventory-v1",
      inventory_claims: inventoryClaims.map((claim, index) => {
        const number = index + 1;
        const row = byNumber.get(number);
        return {
          ...claim,
          claim_number: number,
          candidates: row?.candidates ?? [],
          provider_query: row?.provider_query ?? cleanText(claim?.visual_target),
          provider_queries: row?.provider_queries ?? [cleanText(claim?.visual_target)].filter(Boolean),
          bounded_query_recovery_used: row?.bounded_query_recovery_used === true,
        };
      }),
    };
  }

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
        provider_queries: byNumber.get(Number(segment.segment_number))?.provider_queries ?? [stockQuery],
        bounded_query_recovery_used: byNumber.get(Number(segment.segment_number))?.bounded_query_recovery_used === true,
      })),
    };
  }

  return {
    ...common,
    beats: unitResults.map((row) => ({ scene_number: row.unit_number, candidates: row.candidates })),
  };
}
