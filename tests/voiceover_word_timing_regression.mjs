import assert from 'node:assert/strict';
import { buildVoiceoverWordTiming } from '../services/media-worker/src/voiceover-word-timing.mjs';

for (const text of ['First sentence. Second sentence.', 'Pierwsze zdanie. Drugie zdanie.',
  'Первое предложение. Второе предложение.', 'Перше речення. Друге речення.']) {
  const parts = text.match(/\S+\s*/gu);
  const cues = parts.map((part, i) => ({ part, start: i * 700 + 100, end: i * 700 + 450 }));
  const input = { narration: text, cues, durationSeconds: 3.2, audio: Buffer.from('final audio') };
  const timing = buildVoiceoverWordTiming(input);
  assert.equal(timing.words[2].start_seconds, 1.5, 'must preserve observed pause');
  assert.equal(timing.words.at(-1).end_seconds, 2.55, 'must preserve trailing silence');
  assert.notEqual(timing.audio_sha256, buildVoiceoverWordTiming({ ...input, audio: Buffer.from('different audio') }).audio_sha256);
  assert.throws(() => buildVoiceoverWordTiming({ ...input, cues: cues.slice(1) }), /reconstruct/);
  assert.throws(() => buildVoiceoverWordTiming({ ...input, cues: [] }), /missing/);
  assert.throws(() => buildVoiceoverWordTiming({ ...input, durationSeconds: 2 }), /boundary/);
  assert.throws(() => buildVoiceoverWordTiming({ ...input, cues: cues.map((c, i) => i === 2 ? { ...c, start: 0 } : c) }), /boundary/);
}
console.log('VOICEOVER_WORD_TIMING_REGRESSION_PASS');
