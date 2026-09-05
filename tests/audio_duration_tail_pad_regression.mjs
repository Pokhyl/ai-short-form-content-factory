import assert from 'node:assert/strict';
import fs from 'node:fs';
import { buildNaturalTailPadPlan, MAX_NATURAL_TAIL_PAD_SECONDS } from '../services/media-worker/src/audio-duration-normalization.mjs';

const ru=buildNaturalTailPadPlan(13.248,15);
assert.equal(ru.apply,true);
assert.ok(ru.pad_seconds>0&&ru.pad_seconds<=MAX_NATURAL_TAIL_PAD_SECONDS);
assert.ok(ru.final_duration_seconds>=ru.accepted_min_seconds);
assert.ok(ru.final_duration_seconds<13.6);

const pl=buildNaturalTailPadPlan(26.856,30);
assert.equal(pl.apply,true);
assert.ok(pl.pad_seconds>0&&pl.pad_seconds<=MAX_NATURAL_TAIL_PAD_SECONDS);
assert.ok(pl.final_duration_seconds>=pl.accepted_min_seconds);

assert.equal(buildNaturalTailPadPlan(12.816,15).apply,false,'materially short narration must still go through bounded rewrite recovery');
assert.equal(buildNaturalTailPadPlan(58.656,60).apply,false,'already accepted narration must not be padded');

const server=fs.readFileSync(new URL('../services/media-worker/src/server.mjs',import.meta.url),'utf8');
assert.match(server,/normalizeNaturalVoiceoverTail\(wavPath, targetDurationSeconds\)/);
assert.match(server,/apad=pad_dur=/);
assert.match(server,/tail_pad_seconds/);
const wf=JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF03-natural-edge-voice.json',import.meta.url),'utf8'))[0];
const edgeBody=wf.nodes.find(n=>n.name==='Generate Edge Voiceover').parameters.jsonBody;
assert.match(edgeBody,/target_duration_seconds/);
assert(!JSON.stringify(wf).includes('google_gemini'));
assert(!JSON.stringify(wf).includes('v4-tts-gateway'));
console.log('AUDIO_DURATION_TAIL_PAD_REGRESSION_PASS');
