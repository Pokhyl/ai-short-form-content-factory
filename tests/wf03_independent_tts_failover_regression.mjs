import assert from 'node:assert/strict';import fs from 'node:fs';
const w=JSON.parse(fs.readFileSync('n8n/workflows/WF03-natural-edge-voice.json','utf8'))[0],by=new Map(w.nodes.map(n=>[n.name,n]));
const prep=by.get('Prepare Continuous Voiceover').parameters.jsCode;assert.match(prep,/piper_fallback_voice/);assert.match(prep,/pl_PL-darkman-medium/);assert.match(prep,/uk_UA-mykyta-high/);
const call=by.get('Generate Edge Fallback').parameters;assert.equal(call.url,'http://media-worker:3001/audio/synthesize-free-fallback');assert.match(call.jsonBody,/preferred_provider/);assert.match(call.jsonBody,/self_hosted_piper/);assert.equal(Number(call.options.timeout),280000);
const evaluate=by.get('Evaluate Natural Voiceover').parameters.jsCode;assert.match(evaluate,/self_hosted_piper_faster_whisper/);assert.match(evaluate,/faster-whisper-1\.2\.1-cpu-int8/);assert.match(evaluate,/timedText!==text/);
const apply=by.get('Apply Duration Rewrite').parameters.jsCode;assert.match(apply,/visual-facts-story-v1/);assert.match(apply,/piper_fallback_voice/);
console.log('WF03_INDEPENDENT_TTS_FAILOVER_REGRESSION_PASS');
