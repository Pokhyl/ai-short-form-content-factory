import assert from 'node:assert/strict';
import { buildVisualDiscoveryOptions } from '../services/media-worker/src/visual-discovery-request.mjs';

const canonicalSource = { language: 'uk', title: 'Індукційна плита' };
const timedBeats = [
  {
    scene_number: 1,
    narration: 'Індукційна плита нагріває металевий посуд.',
    narration_support_evidence_ids: ['W1:P1:S1'],
    beat_start_seconds: 0,
    beat_end_seconds: 3,
    duration_seconds: 3,
  },
];

const semantic = buildVisualDiscoveryOptions(
  { canonical_source: canonicalSource, timed_beats: timedBeats },
  { pixabayApiKey: 'pix', pexelsApiKey: 'pex' },
);

assert.equal(semantic.canonicalSource, canonicalSource);
assert.equal(semantic.timedBeats, timedBeats);
assert.equal(semantic.beats, undefined);
assert.equal(semantic.pixabayApiKey, 'pix');
assert.equal(semantic.pexelsApiKey, 'pex');

const legacyBeats = [{ scene_number: 1, visual_target: 'zipper teeth' }];
const legacy = buildVisualDiscoveryOptions({ canonical_source: canonicalSource, beats: legacyBeats });

assert.equal(legacy.canonicalSource, canonicalSource);
assert.equal(legacy.beats, legacyBeats);
assert.equal(legacy.timedBeats, undefined);

console.log('MEDIA_WORKER_VISUAL_DISCOVERY_ADAPTER_REGRESSION_PASS');
