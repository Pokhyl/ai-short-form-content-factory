import assert from 'node:assert/strict';import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF03-natural-edge-voice.json','utf8')),wf=Array.isArray(raw)?raw[0]:raw,by=new Map(wf.nodes.map(n=>[n.name,n]));
const code=by.get('Build Rewrite Narration For Exact Duration Request').parameters.jsCode;
const item={rewrite_prompt:'rewrite',unit_word_targets:[{unit_id:'U1',target_words:9},{unit_id:'U2',target_words:10},{unit_id:'U3',target_words:9}]};
const schema=new Function('$json',code)(item).json.model_request.response_schema;
assert.deepEqual(schema.required,['U1','U2','U3']);assert.equal(schema.properties.U1.minItems,9);assert.equal(schema.properties.U1.maxItems,9);assert.equal(schema.properties.U2.minItems,10);assert.equal(schema.properties.U3.maxItems,9);assert.equal(schema.properties.U2.items.type,'string');assert.match(schema.properties.U2.items.pattern,/A-Za-z/);assert.match(code,/minItems:count,maxItems:count/);assert.doesNotMatch(code,/narration.*type:'string'/);
const eligible=by.get('Require Eligible Voiceover Job').parameters.jsCode;assert.match(eligible,/groundedClaim=clean\(u\.grounded_claim\)/);assert.match(eligible,/!groundedClaim/);
console.log('WF03_DURATION_TOKEN_SCHEMA_REGRESSION_PASS');
