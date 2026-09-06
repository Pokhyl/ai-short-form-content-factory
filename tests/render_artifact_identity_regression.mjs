import assert from 'node:assert/strict';import fs from 'node:fs';
const source=fs.readFileSync('services/media-worker/src/server.mjs','utf8');
assert.match(source,/createHash, randomUUID/);assert.match(source,/visualContract\.version !== "inventory-first-story-v1"/);assert.match(source,/inventory-first-render-v1/);assert.match(source,/full-image-preserve-v1/);assert.match(source,/artifact_sha256: artifactSha256/);assert.match(source,/createHash\("sha256"\)\.update\(outputBytes\)/);
const migration=fs.readFileSync('db/migrations/023_render_artifact_identity.sql','utf8');assert.match(migration,/final_video_sha256/);assert.match(migration,/\^\[0-9a-f\]\{64\}\$/);
console.log('RENDER_ARTIFACT_IDENTITY_REGRESSION_PASS');
