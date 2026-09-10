import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json','utf8'));
const w=Array.isArray(raw)?raw[0]:raw;
const by=new Map(w.nodes.map(n=>[n.name,n]));
const c=w.connections;
for(const [loop,build,review,done] of [
 ['Loop Pre-Claim Review Batches','Build Review Pre-Claim Visual Inventory Request','Review Pre-Claim Visual Inventory','Select Pre-Claim Visual Inventory'],
 ['Loop Inventory Review Batches','Build Review Inventory Candidate Images Request','Review Inventory Candidate Images','Select Verified Claim Inventory'],
]){
 const n=by.get(loop);assert(n,`${loop} missing`);assert.equal(n.type,'n8n-nodes-base.splitInBatches');assert.equal(n.typeVersion,3);assert.equal(n.parameters.batchSize,1);
 assert.deepEqual(c[build].main[0],[{node:loop,type:'main',index:0}],`${build} must enter serial loop`);
 assert.deepEqual(c[loop].main[0],[{node:done,type:'main',index:0}],`${loop} done output must continue after all review responses`);
 assert.deepEqual(c[loop].main[1],[{node:review,type:'main',index:0}],`${loop} loop output must run one reviewer batch`);
 assert.deepEqual(c[review].main[0],[{node:loop,type:'main',index:0}],`${review} success must request the next batch`);
 assert(c[review].main[1]?.some(e=>e.node==='Prepare Planner Failure'),`${review} error branch must remain fail-closed`);
}

assert.match(by.get('Select Pre-Claim Visual Inventory').parameters.jsCode,/pre-claim reviewer unavailable after bounded provider failover/);
assert.match(by.get('Select Verified Claim Inventory').parameters.jsCode,/inventory reviewer unavailable after bounded provider failover/);
console.log('WF02_VISUAL_REVIEW_SERIALIZATION_REGRESSION_PASS');
