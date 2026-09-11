import assert from 'node:assert/strict';import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF03-natural-edge-voice.json','utf8')),wf=Array.isArray(raw)?raw[0]:raw,by=new Map(wf.nodes.map(n=>[n.name,n]));
const code=by.get('Build Rewrite Narration For Exact Duration Request').parameters.jsCode;
const item={rewrite_prompt:'rewrite',unit_order:['U1','U2','U3'],desired_word_target:36,min_unit_words:6};
const req=new Function('$json',code)(item).json.model_request,schema=req.response_schema;
assert.equal(req.route,'storyboard');assert.deepEqual(schema.required,['units']);assert.equal(schema.properties.units.minItems,3);assert.equal(schema.properties.units.maxItems,3);assert.deepEqual(schema.properties.units.items.required,['unit_id','narration']);assert.deepEqual(schema.properties.units.items.properties.unit_id.enum,['U1','U2','U3']);assert.equal(schema.properties.units.items.properties.narration.type,'string');assert.doesNotMatch(code,/properties:\{tokens:/);assert.match(code,/response_format:'json'/);
const eligible=by.get('Require Eligible Voiceover Job').parameters.jsCode;assert.match(eligible,/groundedClaim=clean\(u\.grounded_claim\)/);assert.match(eligible,/!groundedClaim/);
console.log('WF03_DURATION_UNIT_SCHEMA_REGRESSION_PASS');
