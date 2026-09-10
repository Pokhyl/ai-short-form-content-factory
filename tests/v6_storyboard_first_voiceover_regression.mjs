import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF03-natural-edge-voice.json','utf8'));
const wf=Array.isArray(raw)?raw[0]:raw;
const by=new Map(wf.nodes.map((n)=>[n.name,n]));
const serialized=JSON.stringify(wf);
assert.equal(serialized.includes('/webhook/v4-model-gateway'),false,'V6 WF03 must not call legacy model gateway');
assert.equal(serialized.includes('/webhook/v6-model-gateway'),true,'duration rewrite must use V6 free-only model gateway');
for(const name of ['Require Eligible Voiceover Job','Build Exact Story Unit Timings','Prepare Duration Rewrite','Apply Duration Rewrite']){
  const code=by.get(name)?.parameters?.jsCode??'';
  assert.match(code,/storyboard-first-v1/,`${name} must accept storyboard-first-v1`);
  new Function('$','$input',code);
}
assert.equal(by.get('Rewrite Narration For Exact Duration')?.parameters?.url,'http://127.0.0.1:5678/webhook/v6-model-gateway');
const prepare=by.get('Prepare Continuous Voiceover')?.parameters?.jsCode??'';
assert.match(prepare,/microsoft_edge_readaloud/);
assert.match(prepare,/piper_fallback_voice/);
console.log('V6_STORYBOARD_FIRST_VOICEOVER_REGRESSION_PASS');
