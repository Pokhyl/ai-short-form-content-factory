const fs=require('node:fs');

if(process.argv.length!==6 && process.argv.length!==7){
  throw new Error(
    'usage: node scripts/replay_m8_9229.cjs BEFORE_WORKFLOW AFTER_WORKFLOW FIXTURE REPORT [AFTER_OVERLAY]'
  );
}

const beforePath=process.argv[2];
const afterPath=process.argv[3];
const fixturePath=process.argv[4];
const reportPath=process.argv[5];
const afterOverlayPath=process.argv[6]||null;

const beforeWorkflow=JSON.parse(fs.readFileSync(beforePath));
const afterWorkflow=JSON.parse(fs.readFileSync(afterPath));
const fixture=JSON.parse(fs.readFileSync(fixturePath));
const afterOverlay=afterOverlayPath
  ? JSON.parse(fs.readFileSync(afterOverlayPath))
  : null;

const providers=['Pixabay','Pexels','Wikimedia'];
const minScore=55;

function nodeCode(workflow,name){
  const node=workflow.nodes.find(n=>n.name===name);
  if(!node) throw new Error('missing node '+name);
  const code=node.parameters?.jsCode;
  if(typeof code!=='string') throw new Error('node has no jsCode '+name);
  return code;
}

function plannerContexts(workflow){
  const map=new Map();
  for(const provider of providers){
    const code=nodeCode(workflow,'Build '+provider+' Requests');
    const items=new Function('$',code)(
      ()=>({first:()=>({json:fixture.begin})})
    );
    if(!Array.isArray(items)) throw new Error('planner did not return items: '+provider);
    for(const item of items){
      const c=item.json;
      const key=provider+':'+c.shot_uuid+':'+c.query_index;
      if(map.has(key)) throw new Error('duplicate planner context '+key);
      map.set(key,c);
    }
  }
  return map;
}

function normalizeAll(workflow,overlay){
  const contexts=plannerContexts(workflow);
  const overlayMap=new Map();
  if(overlay){
    const rows=Array.isArray(overlay)?overlay:(overlay.responses||[]);
    for(const row of rows){
      const c=row.ctx||{};
      const key=[
        String(row.provider||c.provider||'').toLowerCase(),
        String(c.shot_key||''),
        Number(c.query_index),
        String(c.provider_query||''),
      ].join(':');
      if(overlayMap.has(key)) throw new Error('duplicate overlay row '+key);
      overlayMap.set(key,row);
    }
  }

  const all=[];
  let seq=0;
  let overlayUsed=0;
  for(const row of fixture.responses){
    const key=row.provider+':'+row.ctx.shot_uuid+':'+row.ctx.query_index;
    const ctx=contexts.get(key);
    if(!ctx) throw new Error('missing planned context for saved response '+key);

    const overlayKey=[
      String(row.provider).toLowerCase(),
      String(ctx.shot_key||''),
      Number(ctx.query_index),
      String(ctx.provider_query||''),
    ].join(':');
    const effectiveRow=overlayMap.get(overlayKey)||row;
    if(effectiveRow!==row) overlayUsed++;

    const code=nodeCode(workflow,'Normalize '+row.provider);
    const $=()=>({item:{json:ctx}});
    const result=new Function('$','$json',code)($,effectiveRow.response).json;
    if(!Array.isArray(result.candidates)) {
      throw new Error('normalizer candidates missing '+key);
    }
    for(const candidate of result.candidates){
      const title=
        candidate?.metadata?.title ??
        candidate?.metadata?.alt ??
        candidate?.metadata?.name ??
        null;
      all.push({
        candidate_seq:++seq,
        shot_uuid:ctx.shot_uuid,
        shot_key:ctx.shot_key,
        scene_order:Number(ctx.scene_order),
        query_index:Number(ctx.query_index),
        query:String(ctx.query||''),
        provider_query:String(ctx.provider_query||ctx.query||''),
        domain_context_terms:Array.isArray(ctx.domain_context_terms)
          ? ctx.domain_context_terms.map(String)
          : [],
        provider:String(row.provider).toLowerCase(),
        provider_asset_id:String(candidate.provider_asset_id),
        provider_rank:Number(candidate.provider_rank||999),
        media_type:String(candidate.media_type||''),
        preferred_media_type:String(ctx.preferred_media_type||''),
        source_url:candidate.source_url||null,
        download_url:candidate.download_url||null,
        preview_url:candidate.preview_url||null,
        width:Number(candidate.width||0),
        height:Number(candidate.height||0),
        relevance_score:Number(candidate.relevance_score||0),
        rejected:Boolean(candidate.rejected),
        rejection_reason:candidate.rejection_reason||null,
        title,
        metadata_text:candidate.metadata_text||null,
        visual_intent:ctx.visual_intent,
        must_show:ctx.must_show,
        must_not_show:ctx.must_not_show,
      });
    }
  }
  if(overlay && overlayUsed!==overlayMap.size){
    throw new Error(
      'overlay rows were not all consumed: used '+overlayUsed+' of '+overlayMap.size
    );
  }
  return {contexts,all,overlayUsed};
}

function eligible(c){
  if(c.rejected) return false;
  if(c.provider==='local_diagram') return false;
  if(c.relevance_score<minScore) return false;
  if(c.preferred_media_type==='video' && c.media_type!=='video') return false;
  if(c.preferred_media_type==='photo' && c.media_type!=='photo') return false;
  return true;
}

function cmpCandidate(a,b){
  const aq=a.query_index<=2?0:1;
  const bq=b.query_index<=2?0:1;
  if(aq!==bq) return aq-bq;

  const am=a.media_type===a.preferred_media_type?0:
    (a.preferred_media_type==='diagram'&&a.media_type==='photo'?1:2);
  const bm=b.media_type===b.preferred_media_type?0:
    (b.preferred_media_type==='diagram'&&b.media_type==='photo'?1:2);
  if(am!==bm) return am-bm;

  if(a.relevance_score!==b.relevance_score) return b.relevance_score-a.relevance_score;

  const aa=(a.width>0&&a.height>0)
    ? Math.abs(a.width/a.height-9/16)
    : Number.POSITIVE_INFINITY;
  const ba=(b.width>0&&b.height>0)
    ? Math.abs(b.width/b.height-9/16)
    : Number.POSITIVE_INFINITY;
  if(aa!==ba) return aa-ba;

  if(a.provider_rank!==b.provider_rank) return a.provider_rank-b.provider_rank;

  const aArea=a.width*a.height;
  const bArea=b.width*b.height;
  if(aArea!==bArea) return bArea-aArea;

  if(a.provider!==b.provider) return a.provider.localeCompare(b.provider);
  if(a.provider_asset_id!==b.provider_asset_id) {
    return a.provider_asset_id.localeCompare(b.provider_asset_id,undefined,{numeric:true});
  }
  return a.candidate_seq-b.candidate_seq;
}

function candidateView(c){
  if(!c) return null;
  return {
    shot:c.shot_key,
    provider:c.provider,
    id:c.provider_asset_id,
    query_index:c.query_index,
    query:c.query,
    provider_query:c.provider_query,
    domain_context_terms:c.domain_context_terms,
    score:c.relevance_score,
    rank:c.provider_rank,
    width:c.width,
    height:c.height,
    title:c.title,
    source_url:c.source_url,
    download_url:c.download_url,
    preview_url:c.preview_url,
    rejection_reason:c.rejection_reason,
  };
}

function summarize(label,normalized){
  const shots=fixture.begin.shots_json
    .slice()
    .sort((a,b)=>a.scene_order-b.scene_order||a.shot_order-b.shot_order);

  const perShot=[];
  for(const shot of shots){
    const pool=normalized.all.filter(c=>c.shot_uuid===shot.shot_uuid);
    const ok=pool.filter(eligible).sort(cmpCandidate);
    perShot.push({
      shot:shot.shot_key,
      scene_order:shot.scene_order,
      visual_intent:shot.visual_intent,
      must_show:shot.must_show,
      must_not_show:shot.must_not_show,
      queries_en:shot.queries_en,
      candidate_count:pool.length,
      eligible_count:ok.length,
      top_eligible:candidateView(ok[0]||null),
      top_rejected:pool
        .filter(c=>c.rejected)
        .sort((a,b)=>b.relevance_score-a.relevance_score||cmpCandidate(a,b))
        .slice(0,12)
        .map(candidateView),
    });
  }

  const selected=[];
  const used=new Set();
  let terminalFailure=null;
  for(const shot of shots){
    const pool=normalized.all
      .filter(c=>c.shot_uuid===shot.shot_uuid && eligible(c))
      .filter(c=>!used.has(c.provider+':'+c.provider_asset_id))
      .sort(cmpCandidate);
    const pick=pool[0]||null;
    if(!pick){
      terminalFailure='no compliant relevant visual candidate for shot '+shot.shot_key;
      break;
    }
    selected.push(candidateView(pick));
    used.add(pick.provider+':'+pick.provider_asset_id);
  }

  const contextRows=[...normalized.contexts.values()]
    .sort((a,b)=>
      Number(a.scene_order)-Number(b.scene_order) ||
      String(a.provider).localeCompare(String(b.provider)) ||
      Number(a.query_index)-Number(b.query_index)
    )
    .map(c=>({
      shot:c.shot_key,
      scene_order:c.scene_order,
      provider:c.provider,
      query_index:c.query_index,
      query:c.query,
      provider_query:c.provider_query,
      domain_context_terms:c.domain_context_terms||[],
    }));

  return {
    label,
    candidate_count:normalized.all.length,
    per_shot:perShot,
    production_sequence:{
      selected,
      terminal_failure:terminalFailure,
    },
    contexts:contextRows,
    all_candidates:normalized.all,
  };
}

function candidateKey(c){
  return c.provider+':'+c.provider_asset_id+':'+c.shot_key+':q'+c.query_index;
}

function findRiskCandidates(state){
  const patterns=[
    /Pacific Northwest drought status/i,
    /Peechi/i,
    /HydroelectricTurbineRunner/i,
    /turbine (?:case|casing|pit|governor|shaft|rotor|stator|runner)/i,
    /generator.*(?:manufactur|transport)|(?:manufactur|transport).*generator/i,
    /nameplate|signage|plaque|door/i,
    /air pipe.*penstock|penstock.*air pipe/i,
  ];
  const hits=[];
  for(const c of state.all_candidates){
    const hay=[c.title,c.metadata_text].filter(Boolean).join(' ');
    if(patterns.some(p=>p.test(hay))){
      hits.push(candidateView(c));
    }
  }
  const seen=new Set();
  return hits.filter(c=>{
    const k=c.provider+':'+c.id+':'+c.shot+':'+c.query_index;
    if(seen.has(k)) return false;
    seen.add(k);return true;
  });
}

const beforeNorm=normalizeAll(beforeWorkflow,null);
const afterNorm=normalizeAll(afterWorkflow,afterOverlay);
const before=summarize('before_exact_v53',beforeNorm);
const after=summarize('after_current_worktree',afterNorm);

const beforeBy=new Map(beforeNorm.all.map(c=>[candidateKey(c),c]));
const afterBy=new Map(afterNorm.all.map(c=>[candidateKey(c),c]));
const changed=[];
for(const [k,b] of beforeBy){
  const a=afterBy.get(k);
  if(!a) continue;
  if(
    b.rejected!==a.rejected ||
    b.relevance_score!==a.relevance_score ||
    b.rejection_reason!==a.rejection_reason ||
    b.provider_query!==a.provider_query ||
    JSON.stringify(b.domain_context_terms)!==JSON.stringify(a.domain_context_terms)
  ){
    changed.push({
      key:k,
      before:candidateView(b),
      after:candidateView(a),
    });
  }
}

const report={
  generated_from:{
    before_workflow:beforePath,
    after_workflow:afterPath,
    fixture:fixturePath,
    after_overlay:afterOverlayPath,
    source:fixture.source,
    provider_calls:0,
    production_mutations:0,
    after_overlay_rows_used:afterNorm.overlayUsed,
  },
  before,
  after,
  changed_candidate_rows:changed,
  notable_risks:{
    before:findRiskCandidates(before),
    after:findRiskCandidates(after),
  },
};

fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');

const concise={
  source:report.generated_from.source,
  provider_calls:0,
  before:{
    candidate_count:before.candidate_count,
    per_shot:before.per_shot.map(x=>({
      shot:x.shot,
      eligible:x.eligible_count,
      top:x.top_eligible,
    })),
    production_sequence:before.production_sequence,
  },
  after:{
    candidate_count:after.candidate_count,
    per_shot:after.per_shot.map(x=>({
      shot:x.shot,
      eligible:x.eligible_count,
      top:x.top_eligible,
    })),
    production_sequence:after.production_sequence,
  },
  changed_candidate_rows:changed.length,
  notable_risk_rows_after:report.notable_risks.after.length,
};
console.log(JSON.stringify(concise,null,2));
