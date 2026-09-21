const fs=require('fs');
if(process.argv.length!==6)throw Error('usage: node scripts/replay_visual_candidates.cjs WORKFLOW REPLAY_INPUT REVIEW_EVIDENCE REPORT');
const w=JSON.parse(fs.readFileSync(process.argv[2]));
const replay=JSON.parse(fs.readFileSync(process.argv[3]));
const review=JSON.parse(fs.readFileSync(process.argv[4]));
const contexts=new Map();
for(const provider of ['Pixabay','Pexels','Wikimedia']){
 const code=w.nodes.find(n=>n.name==='Build '+provider+' Requests').parameters.jsCode;
 const items=new Function('$',code)(()=>({first:()=>({json:replay.begin})}));
 for(const {json:c}of items)contexts.set(provider+':'+c.shot_uuid+':'+c.query_index,c);
}
const all=[];
for(const row of replay.responses){
 const ctx=contexts.get(row.provider+':'+row.ctx.shot_uuid+':'+row.ctx.query_index);
 const code=w.nodes.find(n=>n.name==='Normalize '+row.provider).parameters.jsCode;
 const result=new Function('$','$json',code)(()=>({item:{json:ctx}}),row.response).json;
 for(const candidate of result.candidates){
  all.push({shot:ctx.shot_key,query_index:ctx.query_index,provider:row.provider,domain:ctx.domain_context_terms,id:candidate.provider_asset_id,rejected:candidate.rejected,score:candidate.relevance_score,reason:candidate.rejection_reason,title:candidate.metadata?.title||candidate.metadata?.alt});
 }
}
const summary={job_id:review.job_id,provider_calls:0,total_candidates:all.length,shots:[...new Set(all.map(x=>x.shot))].map(shot=>({shot,domain_context_terms:all.find(x=>x.shot===shot).domain,eligible:all.filter(x=>x.shot===shot&&!x.rejected&&x.score>=55).length})),previous_selections:review.selected.map(s=>({scene:s.scene_key,asset_id:s.provider_asset_id,results:all.filter(c=>c.shot===s.scene_key+'-A'&&c.id===s.provider_asset_id)}))};
fs.writeFileSync(process.argv[5],JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify(summary,null,2));
