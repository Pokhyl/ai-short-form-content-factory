import assert from 'node:assert/strict';import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF03-natural-edge-voice.json','utf8')),wf=Array.isArray(raw)?raw[0]:raw,by=new Map(wf.nodes.map(n=>[n.name,n]));
const code=by.get('Build Rewrite Narration For Exact Duration Request').parameters.jsCode;
const item={rewrite_prompt:'rewrite',unit_order:['U1','U2','U3'],desired_word_target:36,min_unit_words:6};
const schema=new Function('$json',code)(item).json.model_request.response_schema;
assert.deepEqual(schema.required,['tokens']);assert.equal(schema.properties.tokens.minItems,36);assert.equal(schema.properties.tokens.maxItems,36);assert.equal(schema.properties.tokens.items.type,'object');assert.deepEqual(schema.properties.tokens.items.required,['unit_id','word']);assert.deepEqual(schema.properties.tokens.items.properties.unit_id.enum,['U1','U2','U3']);assert.equal(schema.properties.tokens.items.properties.word.type,'string');assert.match(schema.properties.tokens.items.properties.word.pattern,/A-Za-z/);assert.match(code,/minItems:desired,maxItems:desired/);assert.doesNotMatch(code,/unit_word_targets/);
const eligible=by.get('Require Eligible Voiceover Job').parameters.jsCode;assert.match(eligible,/groundedClaim=clean\(u\.grounded_claim\)/);assert.match(eligible,/!groundedClaim/);
console.log('WF03_DURATION_TOKEN_SCHEMA_REGRESSION_PASS');
