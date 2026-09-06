import { createHash } from 'node:crypto';

const clean = value => String(value ?? '').normalize('NFKC').replace(/\s+/gu, ' ').trim();

// Edge emits milliseconds for the same continuous synthesis. Never infer missing
// words or divide total audio duration to manufacture alignment.
export function buildVoiceoverWordTiming({ narration, cues, durationSeconds, audio }) {
  const text = clean(narration);
  if (!text || !Array.isArray(cues) || !cues.length) throw new Error('Exact word timing is missing');
  if (!Buffer.isBuffer(audio) || !audio.length) throw new Error('Exact timing requires the final audio bytes');
  const duration = Number(durationSeconds);
  if (!Number.isFinite(duration) || duration <= 0) throw new Error('Invalid measured audio duration');
  if (clean(cues.map(cue => String(cue?.part ?? '')).join('')) !== text) {
    throw new Error('Provider word timing does not reconstruct the narration');
  }
  let previousEnd = 0;
  const words = cues.map((cue, index) => {
    const start = Number(cue.start) / 1000, end = Number(cue.end) / 1000;
    const word = clean(cue.part);
    if (!word || !Number.isFinite(start) || !Number.isFinite(end)
      || start < 0 || end <= start || start < previousEnd || end > duration) {
      throw new Error(`Invalid provider word boundary ${index + 1}`);
    }
    previousEnd = end;
    return { text: word, start_seconds: start, end_seconds: end };
  });
  return {
    version: 'provider-word-timing-v1',
    provider: 'microsoft_edge_readaloud',
    audio_sha256: createHash('sha256').update(audio).digest('hex'),
    script_sha256: createHash('sha256').update(text).digest('hex'),
    duration_seconds: duration,
    words,
  };
}
