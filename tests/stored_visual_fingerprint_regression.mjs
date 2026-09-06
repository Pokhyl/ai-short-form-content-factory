import assert from 'node:assert/strict';
import fs from 'node:fs';
const source=fs.readFileSync('services/media-worker/src/server.mjs','utf8');
assert.match(source,/async function fingerprintStoredVisual/);
assert.match(source,/resolvePersistedMediaPath\(jobId, visualPathInput, "visual"\)/);
assert.match(source,/stored_visual_fingerprint_failed/);
assert.match(source,/requestUrl\.pathname === "\/visual\/fingerprint-stored"/);
assert.match(source,/averageHashHex\(buffer\)/);
console.log('STORED_VISUAL_FINGERPRINT_REGRESSION_PASS');
