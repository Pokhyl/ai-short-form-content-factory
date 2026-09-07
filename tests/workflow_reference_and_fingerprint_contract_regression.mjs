import fs from 'node:fs';
import assert from 'node:assert/strict';
const workflows=fs.readdirSync('n8n/workflows').filter(f=>f.endsWith('.json')).flatMap(f=>JSON.parse(fs.readFileSync('n8n/workflows/'+f)));
function strings(value){return typeof value==='string'?[value]:value&&typeof value==='object'?Object.values(value).flatMap(strings):[];}
for(const w of workflows){
 const names=new Set(w.nodes.map(n=>n.name));
 for(const n of w.nodes)for(const text of strings(n.parameters)){
  for(const match of text.matchAll(/\$\(['"]([^'"]+)['"]\)/g))assert(names.has(match[1]),`${w.name}/${n.name} references removed node ${match[1]}`);
 }
}
const w=workflows.find(w=>w.nodes.some(n=>n.name==='Expand Inventory Fingerprint Items'));
const code=w.nodes.find(n=>n.name==='Expand Inventory Fingerprint Items').parameters.jsCode;
const claims=[{claim_number:1,claim_id:'C1',claim:'A researched claim.',visual_target:'A detailed visible description. '.repeat(15),search_query_en:'mechanical clock escapement',evidence_ids:['S1']}];
const candidate={provider:'wikimedia',provider_asset_id:'fixture',candidate_id:'wikimedia:fixture',preview_urls:['https://example.com/fixture.jpg'],target_anchor_pass:true};
const discovery={inventory_version:'pre-script-visual-inventory-v1',inventory_claims:claims.map(c=>({...c,candidates:[candidate]}))};
const result=new Function('$input','$',code)({first:()=>({json:discovery})},()=>({first:()=>({json:{candidate_claims:claims,research_rows:[{id:'S1'}]}})}))[0].json;
assert.equal(result.local_rank_request.query,claims[0].search_query_en);
assert(result.local_rank_request.query.length<=200,'preview hash API budget must be respected independently of full target length');
assert.equal(result.visual_target,claims[0].visual_target,'full visual acceptance context must not be truncated');
console.log('WORKFLOW_REFERENCE_AND_FINGERPRINT_CONTRACT_PASS');
