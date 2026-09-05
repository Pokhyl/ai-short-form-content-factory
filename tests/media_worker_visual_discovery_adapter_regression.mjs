import assert from 'node:assert/strict';
import fs from 'node:fs';
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
const visualQueriesEn = ['induction cooktop', 'copper induction coil', 'magnetic cookware', 'induction heating diagram'];

const semantic = buildVisualDiscoveryOptions(
  { canonical_source: canonicalSource, timed_beats: timedBeats, visual_queries_en: visualQueriesEn },
  { pixabayApiKey: 'pix', pexelsApiKey: 'pex' },
);

assert.equal(semantic.canonicalSource, canonicalSource);
assert.equal(semantic.timedBeats, timedBeats);
assert.equal(semantic.visualQueriesEn, visualQueriesEn);
assert.equal(semantic.beats, undefined);
assert.equal(semantic.pixabayApiKey, 'pix');
assert.equal(semantic.pexelsApiKey, 'pex');

const legacyBeats = [{ scene_number: 1, visual_target: 'zipper teeth' }];
const legacy = buildVisualDiscoveryOptions({ canonical_source: canonicalSource, beats: legacyBeats });

assert.equal(legacy.canonicalSource, canonicalSource);
assert.equal(legacy.beats, legacyBeats);
assert.equal(legacy.timedBeats, undefined);
assert.equal(legacy.visualQueriesEn, undefined);

const discoverySource=fs.readFileSync(new URL('../services/media-worker/src/visual-discovery.mjs',import.meta.url),'utf8');
assert.match(discoverySource,/Number\(segment\.segment_number\) - 1/,'visual queries must bind one-to-one to final narration beats');
assert.doesNotMatch(discoverySource,/index \* groundedQueries\.length \/ segmentation\.segments\.length/);
assert.match(discoverySource,/narration-beat-visual-segments-v4/,'timed visual segments must remain beat-aligned');

console.log('MEDIA_WORKER_VISUAL_DISCOVERY_ADAPTER_REGRESSION_PASS');
