const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const code=workflow.nodes.find(n=>n.name==='Validate Timing Precision Retry').parameters.jsCode;

function response(narrations){
  return {
    statusCode:200,
    body:{
      candidates:[{content:{parts:[{text:JSON.stringify({narrations})}]}}],
      usageMetadata:{promptTokenCount:10,candidatesTokenCount:10,totalTokenCount:20},
    },
  };
}

function run({original,base,candidate,language='pl'}){
  const ctx={
    script_run_id:'run',
    model:'test',
    base_storyboard:{
      narration:base.join(' '),
      scenes:base.map((narration,i)=>({
        scene_id:'S'+(i+1),
        narration,
        shots:[{shot_id:'S'+(i+1)+'-A'}],
      })),
    },
    prior_usage:{},
    target_scene_word_counts:base.map(x=>x.split(/\s+/u).length),
  };
  const rows={
    'Build Timing Precision Retry':ctx,
    'Build Script Prompt':{
      language_code:language,
      target_duration_seconds:15,
      word_min:10,
      word_max:40,
    },
    'Normalize Timing Probe':{
      storyboard:{
        narration:original.join(' '),
        scenes:original.map((narration,i)=>({
          scene_id:'S'+(i+1),
          narration,
          shots:[{shot_id:'S'+(i+1)+'-A'}],
        })),
      },
    },
  };
  const $=name=>({first:()=>({json:rows[name]})});
  return new Function('$','$json',code)($,response(candidate)).json;
}

test('9438 regression: novel filler in one precision scene falls back to a valid prior scene instead of being accepted',()=>{
  const original=[
    'Woda gromadzona jest w zbiorniku za zaporą.',
    'Spadająca rzeka napędza turbinę wodną.',
    'Obrotowy ruch turbiny napędza generator prądu elektrycznego.',
    'Gotowy prąd trafia do sieci.',
    'To czysta energia.',
  ];
  const base=[
    'Woda gromadzona jest w zbiorniku za zaporą.',
    'Spadająca rzeka napędza turbinę.',
    'Turbina napędza generator prądu.',
    'Prąd trafia do sieci.',
    'To czysta energia.',
  ];
  const candidate=[
    original[0],
    'Spadająca rzeka potężnie napędza turbinę wodną.',
    original[2],
    original[3],
    original[4],
  ];
  const out=run({original,base,candidate});
  assert.equal(out.precision_semantic_fallback_used,true);
  assert.deepEqual(out.precision_semantic_sources,[
    'precision','base','precision','precision','precision'
  ]);
  assert.equal(out.storyboard.scenes[1].narration,base[1]);
  assert.doesNotMatch(out.storyboard.narration,/potężnie/u);
  assert.equal(out.narration_word_count,26);
});

test('precision fallback never accepts a semantically invalid base scene; immutable original is the final safe fallback',()=>{
  const original=[
    'Zapora zatrzymuje rzekę, tworząc zbiornik.',
    'Woda napędza turbinę wodną.',
  ];
  const base=[
    'Samochody jadą szeroką drogą.',
    'Woda napędza turbinę wodną.',
  ];
  const candidate=[
    'Ogromne samochody jadą szeroką drogą.',
    'Woda napędza turbinę wodną.',
  ];
  const out=run({original,base,candidate});
  assert.equal(out.precision_semantic_fallback_used,true);
  assert.equal(out.precision_semantic_sources[0],'original');
  assert.equal(out.storyboard.scenes[0].narration,original[0]);
});

test('valid precision lines remain untouched and do not report semantic fallback',()=>{
  const original=[
    'Zapora zatrzymuje rzekę, tworząc zbiornik.',
    'Woda napędza turbinę wodną.',
  ];
  const candidate=[...original];
  const out=run({original,base:original,candidate});
  assert.equal(out.precision_semantic_fallback_used,false);
  assert.deepEqual(out.precision_semantic_sources,['precision','precision']);
  assert.deepEqual(out.storyboard.scenes.map(x=>x.narration),candidate);
});
