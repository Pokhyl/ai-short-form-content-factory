import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json','utf8'));
const wf=Array.isArray(raw)?raw[0]:raw;
const nodes=new Map(wf.nodes.map(n=>[n.name,n]));
for(const name of ['Validate Candidate Claims','Validate Visual Exploration']){
  const code=nodes.get(name)?.parameters?.jsCode??'';
  assert.doesNotMatch(code,/\\bshow\(\?:ing\|s\)\?\\b/,'show/showing/shows must not be blanket-rejected inside an observable noun phrase');
  assert.match(code,/\\bclose\[ -\]\?up\\b/);
  assert.match(code,/\\bduring \(\?:operation\|use\)\\b/);
}
const claimCode=nodes.get('Validate Candidate Claims').parameters.jsCode;
assert.match(claimCode,/visualWords\.length<2\|\|visualWords\.length>10/);
assert.match(claimCode,/not represented in cited real inventory/);
const explorationCode=nodes.get('Validate Visual Exploration').parameters.jsCode;
assert.match(explorationCode,/words\.length<2\|\|words\.length>10/);
assert.match(explorationCode,/lost resolved-subject identity/);
const phrase='map showing canal path';
assert.equal(phrase.split(/\s+/u).length,4);
console.log('WF02_OBSERVABLE_TARGET_LEXICAL_REGRESSION_PASS');
