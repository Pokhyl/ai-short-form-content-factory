import assert from 'node:assert/strict';
import fs from 'node:fs';
const dockerfile=fs.readFileSync(new URL('../services/media-worker/Dockerfile',import.meta.url),'utf8');
const pkg=JSON.parse(fs.readFileSync(new URL('../services/media-worker/package.json',import.meta.url),'utf8'));
assert.match(dockerfile,/COPY package\.json package-lock\.json/);
assert.match(dockerfile,/npm ci --omit=dev/);
assert(pkg.dependencies?.sharp,'sharp must be declared for preview hashing and image normalization');
assert(pkg.dependencies?.['node-edge-tts'],'node-edge-tts must be declared for free fallback TTS');
console.log('MEDIA_WORKER_CONTAINER_BUILD_CONTRACT_REGRESSION_PASS');
