import assert from 'node:assert/strict';import fs from 'node:fs';
const server=fs.readFileSync('services/media-worker/src/server.mjs','utf8'),mod=fs.readFileSync('services/media-worker/src/piper-whisper-fallback.mjs','utf8'),docker=fs.readFileSync('services/media-worker/Dockerfile','utf8');
for(const x of ['self_hosted_piper','PIPER_ALIGNMENT_PROVIDER','PIPER_MODEL_VERSION','preferredProvider','synthesizePiperWhisper'])assert.ok(server.includes(x),`server missing ${x}`);
assert.match(server,/for \(let attempt = 1; attempt <= 2; attempt \+= 1\)/);assert.match(server,/preferredProvider !== "self_hosted_piper"/);assert.match(server,/wordTiming = \{/);assert.match(server,/provider: PIPER_ALIGNMENT_PROVIDER/);
for(const x of ['piper-tts-1.2.0','faster-whisper-1.2.1-cpu-int8','536b0662742c02347bc0e980a01041f333bce120','pl_PL-darkman-medium','uk_UA-mykyta-high'])assert.ok(mod.includes(x),`module missing ${x}`);
for(const x of ['piper-tts==1.2.0','faster-whisper==1.2.1','download_tts_models.py','COPY python ./python'])assert.ok(docker.includes(x),`Dockerfile missing ${x}`);
assert.ok(!docker.includes('piper-tts==1.8.0'),'GPL Piper 1.8 must not enter the runtime image');
console.log('MEDIA_WORKER_INDEPENDENT_TTS_CONTRACT_REGRESSION_PASS');
