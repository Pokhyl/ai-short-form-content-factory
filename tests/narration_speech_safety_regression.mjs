import assert from 'node:assert/strict';import fs from 'node:fs';
const one=p=>{const r=JSON.parse(fs.readFileSync(p,'utf8'));return Array.isArray(r)?r[0]:r};
const n2=new Map(one('n8n/workflows/WF02-plan-script-and-scenes.json').nodes.map(n=>[n.name,n]));const n3=new Map(one('n8n/workflows/WF03-natural-edge-voice.json').nodes.map(n=>[n.name,n]));
const final=n2.get('Build Final Inventory Story').parameters.jsCode,prep=n3.get('Prepare Duration Rewrite').parameters.jsCode,apply=n3.get('Apply Duration Rewrite').parameters.jsCode;
for(const code of [final,apply]){assert.match(code,/replace\(\/\\s\+\\\/\\s\+\/gu/);assert.match(code,/replace\(\/\\s\+\\\|\\s\+\/gu/);assert.match(code,/replace\(\/\\s\+\(\?:→\|->\)\\s\+\/gu/);}
assert.match(prep,/no headings, citations, slash separators, pipes, arrows, bullets or markdown/);
console.log('NARRATION_SPEECH_SAFETY_REGRESSION_PASS');
