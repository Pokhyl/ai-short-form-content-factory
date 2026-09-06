import assert from 'node:assert/strict';
import fs from 'node:fs';

const wf02=JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF02-plan-script-and-scenes.json',import.meta.url),'utf8'))[0];
const wf04=JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF04-visual-sourcing.json',import.meta.url),'utf8'))[0];
const n2=new Map(wf02.nodes.map(n=>[n.name,n]));
const n4=new Map(wf04.nodes.map(n=>[n.name,n]));

assert.match(n2.get('Persist Grounded AI Narration').parameters.query,/visual_search_queries_en/);
assert.match(n4.get('Load Visual Context').parameters.query,/visual_search_queries_en/);
assert.match(n4.get('Require Eligible Visual Job').parameters.jsCode,/Grounded English visual query inventory is missing/);
assert.match(n4.get('Prepare Canonical Media Request').parameters.jsCode,/visual_queries_en:j\.visual_search_queries_en/);
const expandCode=n4.get('Expand Rank Items').parameters.jsCode;
assert.match(expandCode,/plan\.visual_target\|\|plan\.canonical_subject/);
assert.doesNotMatch(expandCode,/plan\.visual_description/);
const attachCode=n4.get('Attach Rank Results').parameters.jsCode;
assert.doesNotMatch(attachCode,/MIN_VISUAL_RELEVANCE|metadata_overlap.*0\.018/);
assert.match(attachCode,/Local visual fingerprinting/);

const prepareNode=n4.get('Prepare Multimodal Visual Review');
const reviewNode=n4.get('Require Multimodal Visual Selection');
const prepareCode=prepareNode.parameters.jsCode;
const reviewCode=reviewNode.parameters.jsCode;
assert.match(prepareCode,/Candidate filenames, provider IDs and metadata are intentionally hidden/);
assert.match(prepareCode,/visible_description/);
assert.match(prepareCode,/visual_review_id/);
assert.doesNotMatch(prepareCode,/candidate \$\{i\+1\}: \$\{c\.candidate_id\}/);
assert.match(prepareCode,/batchSize=6/);
assert.match(prepareCode,/Math\.min\(4,/);
assert.match(reviewCode,/verdicts/);
assert.match(reviewCode,/visibleMeta/);
assert.match(reviewCode,/targetPass/);
assert.match(reviewCode,/visual_review_grounded_reject_count/);
assert.match(n4.get('Merge Conflict Recovery Approval').parameters.jsCode,/unreviewed fallback is forbidden/);
assert.equal(prepareNode.parameters.mode,'runOnceForAllItems');
assert.equal(reviewNode.parameters.mode,'runOnceForAllItems');
assert.equal(n4.get('Inline Candidate Images').parameters.url,'http://media-worker:3001/visual/inline-review-images');
assert.match(n4.get('Review Actual Candidate Images').parameters.jsonBody,/verdicts/);
assert.match(n4.get('Review Actual Candidate Images').parameters.jsonBody,/visible_description/);
assert.equal(wf04.connections['Inline Candidate Images'].main[1][0].node,'Prepare Visual Failure');
assert.equal(wf04.connections['Review Actual Candidate Images'].main[1][0].node,'Prepare Visual Failure');

const candidate=(id,title,targetPass=true)=>({
  candidate_id:id,provider:'fixture',provider_asset_id:id,media_kind:'photo',
  preview_url:`https://example.test/${id}.jpg`,preview_urls:[`https://example.test/${id}.jpg`],
  title,description:title,categories:title,metadata:{retrieval_source:'fixture_search',source_title:title,source_description:title,source_tags:title},
  target_anchor_pass:targetPass,visual_hash:'a'.repeat(64),selection_utility:0.9,
});
const good1=candidate('photo:good1','copper transformer coil winding around iron core',true);
const good2=candidate('photo:good2','copper wire transformer winding and iron core',true);
const school=candidate('photo:school','neoclassical school building stone columns',false);
const hallucination=candidate('photo:hallucination','neoclassical school building blue door',true);
const baseSegment={
  job_id:'00000000-0000-4000-8000-000000000001',segment_number:1,expected_visual_segment_count:1,
  planned_shot_count:2,canonical_subject:'Electric transformer',visual_target:'copper transformer coil winding',
  narration:'Current flows through the copper transformer coil.',ranked_candidates:[good1,good2,school,hallucination],
};
const prepareReview=new Function('$input',prepareCode);
const prepared=prepareReview({all:()=>[{json:baseSegment}]})[0].json;
assert.equal(prepared.segments[0].visual_review_candidates.length,4);
assert.deepEqual(prepared.segments[0].visual_review_candidates.map(c=>c.visual_review_id),['S1-C1','S1-C2','S1-C3','S1-C4']);
const textItems=prepared.visual_review_request.input.filter(x=>x.type==='text').map(x=>x.text).join('\n');
for(const id of ['photo:good1','photo:good2','photo:school','photo:hallucination'])assert.ok(!textItems.includes(id),'provider candidate IDs must be hidden from model prompt');
assert.ok(textItems.includes('REVIEW S1-C1'));

const review=new Function('$input','$',reviewCode);
const review$=name=>{assert.equal(name,'Prepare Multimodal Visual Review');return {all:()=>[{json:prepared}]}};
const response={segments:[{segment_number:1,verdicts:[
  {review_id:'S1-C1',relevant:true,visible_description:'copper transformer coil winding around iron core'},
  {review_id:'S1-C2',relevant:true,visible_description:'copper wire transformer winding and iron core'},
  {review_id:'S1-C3',relevant:false,visible_description:'neoclassical school building with stone columns'},
  {review_id:'S1-C4',relevant:true,visible_description:'copper transformer coil laboratory equipment'},
]}]};
const reviewed=review({all:()=>[{json:{text:JSON.stringify(response),model:'fixture'}}]},review$)[0].json;
assert.deepEqual(reviewed.ranked_candidates.map(c=>c.candidate_id),['photo:good1','photo:good2']);
assert.equal(reviewed.visual_review_shortfall,false);
assert.equal(reviewed.visual_review_approved_count,2);
assert.equal(reviewed.visual_review_model_relevant_count,3);
assert.equal(reviewed.visual_review_grounded_reject_count,1,'hallucinated description inconsistent with provider metadata must be rejected');
assert.equal(reviewed.ranked_candidates[0].multimodal_visible_description,'copper transformer coil winding around iron core');

const zero={segments:[{segment_number:1,verdicts:prepared.segments[0].visual_review_candidates.map(c=>({review_id:c.visual_review_id,relevant:false,visible_description:'unrelated visible object'}))}]};
const zeroReviewed=review({all:()=>[{json:{text:JSON.stringify(zero),model:'fixture'}}]},review$)[0].json;
assert.equal(zeroReviewed.visual_review_shortfall,true);
assert.equal(zeroReviewed.visual_review_approved_count,0);
assert.deepEqual(zeroReviewed.ranked_candidates,[]);

const longSegments=Array.from({length:18},(_,i)=>({json:{
  ...baseSegment,segment_number:i+1,expected_visual_segment_count:18,visual_target:`target ${i+1}`,
  ranked_candidates:Array.from({length:10},(_,j)=>candidate(`photo:${i+1}:${j+1}`,`target ${i+1} exact visible object ${j+1}`,true)),
}}));
const batches=prepareReview({all:()=>longSegments});
assert.equal(batches.length,3);
assert(batches.every(x=>x.json.visual_review_request.input.length===55),'six-segment batch must remain 24 images / 55 items');
assert(batches.flatMap(x=>x.json.segments).every(s=>s.visual_review_candidates.length===4));

assert.match(n4.get('Choose Visual Assignment').parameters.jsCode,/assetCount>1\)continue/);
assert.throws(()=>review({all:()=>[{json:{text:'not-json'}}]},review$),/returned invalid JSON/);
for(const node of [...wf02.nodes,...wf04.nodes].filter(n=>n.type==='n8n-nodes-base.code'))new Function('$input','$',node.parameters.jsCode);
console.log('WF04_PHOTO_RELEVANCE_GATE_REGRESSION_PASS');
