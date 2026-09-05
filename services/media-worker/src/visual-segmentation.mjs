const DEFAULT_SEGMENTATION = Object.freeze({
  min_segment_seconds: 2.4,
  support_change_min_seconds: 3.2,
  preferred_segment_seconds: 5.5,
  max_segment_seconds: 8.5,
  max_visual_cluster_duration_share: 0.34,
});

function cleanText(value) {
  return String(value ?? "")
    .normalize("NFKC")
    .replace(/\s+/gu, " ")
    .trim();
}

function supportIds(value) {
  if (!Array.isArray(value)) return [];
  return [...new Set(value.map((item) => cleanText(item)).filter(Boolean))];
}

function supportSignature(value) {
  return [...supportIds(value)].sort().join("|");
}

function endsNaturalUnit(text) {
  return /[.!?…][\]})»”"']*$/u.test(cleanText(text));
}

function endsClauseUnit(text) {
  return /[;:][\]})»”"']*$/u.test(cleanText(text));
}

function normalizeBeat(beat, index, previousEnd) {
  if (beat === null || typeof beat !== "object" || Array.isArray(beat)) {
    throw new Error(`timed beat ${index + 1} must be an object`);
  }
  const sceneNumber = Number(beat.scene_number ?? beat.beat_number);
  const start = Number(beat.beat_start_seconds ?? beat.start_seconds);
  const end = Number(beat.beat_end_seconds ?? beat.end_seconds);
  const duration = Number(beat.duration_seconds);
  const narration = cleanText(beat.narration);
  const evidenceIds = supportIds(beat.narration_support_evidence_ids ?? beat.support_evidence_ids);
  if (!Number.isInteger(sceneNumber) || sceneNumber !== index + 1) throw new Error(`timed beat ${index + 1} number is invalid`);
  if (!Number.isFinite(start) || !Number.isFinite(end) || !Number.isFinite(duration) || start < 0 || end <= start || duration <= 0) throw new Error(`timed beat ${sceneNumber} timing is invalid`);
  if (Math.abs(start - previousEnd) > 0.012 || Math.abs((end - start) - duration) > 0.012) throw new Error(`timed beat ${sceneNumber} timing is not contiguous`);
  if (!narration) throw new Error(`timed beat ${sceneNumber} narration is empty`);
  if (!evidenceIds.length) throw new Error(`timed beat ${sceneNumber} evidence is empty`);
  return { scene_number: sceneNumber, start_seconds: start, end_seconds: end, duration_seconds: duration, narration, support_evidence_ids: evidenceIds };
}

function contentTokens(text) {
  const common = new Set([
    "the","and","with","from","that","this","into","through","what","when","where","which","does","work","works","have","has","are","was","were","for","of","to","in","on","by","a","an",
    "oraz","które","który","która","jest","przez","dla","jak","dlaczego","podczas","się","sie","or","lub","albo","nie","na","do","z","w",
    "который","которая","которые","через","для","как","почему","что","это","при","или","и","в","на","из","с","со","не",
    "який","яка","які","через","для","як","чому","що","це","при","або","і","та","в","у","на","із","з","зі","не",
  ]);
  return (cleanText(text).toLocaleLowerCase().match(/[\p{L}\p{N}]+/gu) ?? [])
    .filter((token) => token.length >= 4 && !common.has(token));
}

export function deriveVisualSearchTerms(text, limit = 2) {
  const raw = contentTokens(text);
  const unique = [];
  for (let i = 0; i < raw.length; i += 1) {
    const token = raw[i];
    if (unique.some((item) => item.token === token)) continue;
    const previous = i > 0 ? raw[i - 1] : null;
    const phrase = previous && previous !== token ? `${previous} ${token}` : token;
    unique.push({ token, phrase, score: token.length + (i / Math.max(1, raw.length)) * 2 });
  }
  unique.sort((a, b) => b.score - a.score || b.token.length - a.token.length || a.token.localeCompare(b.token));
  const out = [];
  for (const item of unique) {
    const value = cleanText(item.phrase).slice(0, 80);
    if (!value || out.some((existing) => existing.toLocaleLowerCase() === value.toLocaleLowerCase())) continue;
    out.push(value);
    if (out.length >= limit) break;
  }
  return out;
}

function closeSegment(buffer, segments) {
  if (!buffer.length) return;
  const first = buffer[0], last = buffer[buffer.length - 1];
  const evidence = [];
  for (const beat of buffer) for (const id of beat.support_evidence_ids) if (!evidence.includes(id)) evidence.push(id);
  const narration = cleanText(buffer.map((beat) => beat.narration).join(" "));
  const duration = last.end_seconds - first.start_seconds;
  segments.push({
    segment_number: segments.length + 1,
    first_scene_number: first.scene_number,
    last_scene_number: last.scene_number,
    start_seconds: Number(first.start_seconds.toFixed(6)),
    end_seconds: Number(last.end_seconds.toFixed(6)),
    duration_seconds: Number(duration.toFixed(6)),
    narration,
    support_evidence_ids: evidence,
    search_terms: deriveVisualSearchTerms(narration, 2),
  });
}

export function buildVisualSegments(timedBeats, options = {}) {
  const cfg = { ...DEFAULT_SEGMENTATION, ...options };
  for (const key of ["min_segment_seconds","support_change_min_seconds","preferred_segment_seconds","max_segment_seconds"]) {
    const value = Number(cfg[key]);
    if (!Number.isFinite(value) || value <= 0) throw new Error(`${key} must be positive`);
    cfg[key] = value;
  }
  if (!(cfg.min_segment_seconds <= cfg.support_change_min_seconds && cfg.support_change_min_seconds <= cfg.preferred_segment_seconds && cfg.preferred_segment_seconds < cfg.max_segment_seconds)) {
    throw new Error("visual segmentation thresholds are inconsistent");
  }
  cfg.max_visual_cluster_duration_share = Number(cfg.max_visual_cluster_duration_share);
  if (!Number.isFinite(cfg.max_visual_cluster_duration_share) || cfg.max_visual_cluster_duration_share <= 0 || cfg.max_visual_cluster_duration_share > 1) {
    throw new Error("max_visual_cluster_duration_share must be in (0, 1]");
  }
  if (!Array.isArray(timedBeats) || timedBeats.length === 0 || timedBeats.length > 100) throw new Error("timed beats must contain between 1 and 100 items");
  const beats = [];
  let previousEnd = 0;
  for (let i = 0; i < timedBeats.length; i += 1) {
    const beat = normalizeBeat(timedBeats[i], i, previousEnd);
    beats.push(beat);
    previousEnd = beat.end_seconds;
  }

  const totalDuration = previousEnd;
  const qualityMaxSegmentSeconds = totalDuration * cfg.max_visual_cluster_duration_share;
  const effectiveMaxSegmentSeconds = Math.min(cfg.max_segment_seconds, qualityMaxSegmentSeconds);
  if (!Number.isFinite(effectiveMaxSegmentSeconds) || effectiveMaxSegmentSeconds <= 0) throw new Error("effective visual segment maximum is invalid");
  for (const beat of beats) {
    if (beat.duration_seconds > effectiveMaxSegmentSeconds + 0.02) {
      throw new Error(`timed beat ${beat.scene_number} exceeds visual quality segment duration cap`);
    }
  }

  const segments = [];
  let buffer = [];
  for (let index = 0; index < beats.length; index += 1) {
    const beat = beats[index];
    if (buffer.length) {
      const prospective = beat.end_seconds - buffer[0].start_seconds;
      if (prospective > effectiveMaxSegmentSeconds + 0.001) {
        closeSegment(buffer, segments);
        buffer = [];
      }
    }
    buffer.push(beat);
    const duration = buffer[buffer.length - 1].end_seconds - buffer[0].start_seconds;
    const next = beats[index + 1] ?? null;
    const supportChanges = next ? supportSignature(beat.support_evidence_ids) !== supportSignature(next.support_evidence_ids) : true;
    const natural = endsNaturalUnit(beat.narration);
    const clause = endsClauseUnit(beat.narration);
    const shouldClose =
      duration >= effectiveMaxSegmentSeconds - 0.001 ||
      (duration >= cfg.min_segment_seconds && natural) ||
      (duration >= cfg.support_change_min_seconds && supportChanges) ||
      (duration >= cfg.preferred_segment_seconds && clause) ||
      duration >= cfg.preferred_segment_seconds;
    if (shouldClose) {
      closeSegment(buffer, segments);
      buffer = [];
    }
  }
  if (buffer.length) closeSegment(buffer, segments);

  if (segments.length > 1) {
    const last = segments[segments.length - 1];
    const previous = segments[segments.length - 2];
    if (last.duration_seconds < cfg.min_segment_seconds && previous.duration_seconds + last.duration_seconds <= effectiveMaxSegmentSeconds + 0.001) {
      const merged = beats.slice(previous.first_scene_number - 1, last.last_scene_number);
      segments.splice(segments.length - 2, 2);
      closeSegment(merged, segments);
    }
  }

  let cursor = 0;
  for (let i = 0; i < segments.length; i += 1) {
    const segment = segments[i];
    segment.segment_number = i + 1;
    if (Math.abs(segment.start_seconds - cursor) > 0.012) throw new Error(`visual segment ${i + 1} starts with a gap`);
    if (segment.duration_seconds > effectiveMaxSegmentSeconds + 0.02) throw new Error(`visual segment ${i + 1} exceeds quality-constrained maximum duration`);
    // Use two distinct full-screen stills for a normal-length semantic segment.
    // Very short segments keep one still so cuts never become unreadably fast.
    segment.planned_shot_count = segment.duration_seconds >= 3 ? 2 : 1;
    cursor = segment.end_seconds;
  }
  if (Math.abs(cursor - previousEnd) > 0.012) throw new Error("visual segments do not cover the full timed-beat duration");

  return {
    version: "semantic-visual-segments-v3",
    config: { ...cfg, quality_max_segment_seconds: Number(qualityMaxSegmentSeconds.toFixed(6)), effective_max_segment_seconds: Number(effectiveMaxSegmentSeconds.toFixed(6)) },
    duration_seconds: Number(previousEnd.toFixed(6)),
    segment_count: segments.length,
    segments,
  };
}

export const visualSegmentationDefaults = DEFAULT_SEGMENTATION;
