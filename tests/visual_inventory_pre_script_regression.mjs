import assert from 'node:assert/strict';
import fs from 'node:fs';
import { buildVisualDiscoveryOptions } from '../services/media-worker/src/visual-discovery-request.mjs';

const body={inventory_claims:[{claim_number:1,claim:'A complete factual claim.',evidence_ids:['S1'],visual_target:'mechanical clock escapement'}]};
const opts=buildVisualDiscoveryOptions(body,{pixabayApiKey:'p',pexelsApiKey:'x'});
assert.deepEqual(opts.inventoryClaims,body.inventory_claims);
const source=fs.readFileSync(new URL('../services/media-worker/src/visual-discovery.mjs',import.meta.url),'utf8');
assert.match(source,/pre-script-visual-inventory-v1/);
assert.match(source,/inventory_claims must be sequential complete claims/);
assert.match(source,/segmentedMode \|\| inventoryMode/);
assert.match(source,/withCandidateAnchorMetrics/);
assert.match(source,/inventory_recovery_query_count/);
console.log('VISUAL_INVENTORY_PRE_SCRIPT_REGRESSION_PASS');
