import assert from 'node:assert/strict';
import fs from 'node:fs';
import { buildProviderTailTrimPlan, FRAME_TOLERANCE_SECONDS } from '../services/media-worker/src/audio-duration-normalization.mjs';

const panama=buildProviderTailTrimPlan(16.704,15.775);
assert.equal(panama.apply,true);
assert.equal(panama.last_word_end_seconds,15.775);
assert.ok(Math.abs(panama.final_duration_seconds-(15.775+FRAME_TOLERANCE_SECONDS))<1e-6);
assert.ok(panama.trim_seconds>0.89&&panama.trim_seconds<0.90);

const alreadyTight=buildProviderTailTrimPlan(15.8,15.775);
assert.equal(alreadyTight.apply,false);
assert.equal(alreadyTight.trim_seconds,0);

assert.throws(()=>buildProviderTailTrimPlan(15,15.1),/exceeds measured audio duration/);

const server=fs.readFileSync(new URL('../services/media-worker/src/server.mjs',import.meta.url),'utf8');
assert.match(server,/providerCues = JSON\.parse/);
assert.match(server,/trimProviderTrailingSilence\(wavPath, providerCues\)/);
assert.match(server,/normalizeNaturalVoiceoverTail\(wavPath, targetDurationSeconds\)/);
assert.match(server,/providerCues = JSON\.parse[\s\S]{0,900}trimProviderTrailingSilence\(wavPath, providerCues\)[\s\S]{0,500}normalizeNaturalVoiceoverTail\(wavPath, targetDurationSeconds\)/,'provider tail trim must precede duration padding/gating in the Edge synthesis path');
assert.match(server,/provider_tail_trim_seconds/);
assert.match(server,/provider_last_word_end_seconds/);
console.log('AUDIO_PROVIDER_TAIL_TRIM_REGRESSION_PASS');
