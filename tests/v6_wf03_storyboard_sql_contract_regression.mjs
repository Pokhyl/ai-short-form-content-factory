import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF03-natural-edge-voice.json','utf8'));const wf=Array.isArray(raw)?raw[0]:raw;const by=new Map(wf.nodes.map(n=>[n.name,n]));
const stale="IN ('inventory-first-story-v1','visual-facts-story-v1')";
const accepted="IN ('inventory-first-story-v1','visual-facts-story-v1','storyboard-first-v1')";
const persist=by.get('Persist Voiceover Result').parameters.query;
const rewrite=by.get('Persist Duration Rewrite').parameters.query;
assert.equal(persist.includes(stale),false);
assert.equal(rewrite.includes(stale),false);
assert.equal((persist.match(/storyboard-first-v1/g)||[]).length,2,'voiceover persist must admit storyboard-first in locked and ok predicates');
assert.equal((rewrite.match(/storyboard-first-v1/g)||[]).length,1,'duration rewrite persist must admit storyboard-first');
assert.ok(persist.includes(accepted));
assert.ok(rewrite.includes(accepted));
for(const n of wf.nodes){const q=n.parameters?.query;if(typeof q==='string')assert.equal(q.includes(stale),false,`stale two-version SQL gate remains in ${n.name}`);}
console.log('V6_WF03_STORYBOARD_SQL_CONTRACT_PASS');
