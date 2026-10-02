const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map(n=>[n.name,n]));
const response=result=>({
  statusCode:200,
  body:{candidates:[{content:{parts:[{text:JSON.stringify(result)}]}}]},
});

const source={
  storyboard:{
    narration:'Poziomica pomaga w pracy. Narzędzie wskazuje poziom. Ułatwia ustawienie elementów.',
    scenes:[{
      scene_id:'S3',
      narration:'Poziomica pomaga w pracy.',
      shots:[{
        shot_id:'S3-A',
        visual_intent:'A construction worker holding a poziomica during building renovation work.',
        must_show:['poziomica'],
        must_not_show:['laser level'],
        queries_en:[
          'construction worker using poziomica',
          'poziomica in building renovation',
          'poziomica',
        ],
        preferred_media_type:'photo',
      }],
    }],
  },
  accepted_voiceover_candidate:{audio_base64:'same-audio',audio_sha256:'same-hash'},
};
const promptCtx={language_code:'pl',target_duration_seconds:30};

function buildFinal(){
  const $=name=>({first:()=>({json:name==='Build Script Prompt'?promptCtx:{}})});
  return new Function('$','$json',byName['Build Narration Language Review Final'].parameters.jsCode)($,structuredClone(source)).json;
}

test('11790 final review includes all visual metadata and requires visual repairs array',()=>{
  const built=buildFinal();
  assert.equal(built.visual_records.length,1);
  assert.equal(built.visual_records[0].shot_id,'S3-A');
  assert.equal(built.visual_records[0].must_show[0],'poziomica');
  assert.match(built.system_message,/ASCII-only source-language words still count as foreign lexical items/);
  assert.deepEqual(
    built.response_json_schema.required,
    ['language','issues','visual_repairs']
  );
});

test('11790 final review translates ASCII Polish visual metadata without changing narration or structure',()=>{
  const built=buildFinal();
  const provider=response({
    language:'pl',
    issues:[],
    visual_repairs:[{
      scene_id:'S3',
      shot_id:'S3-A',
      visual_intent:'A construction worker holding a spirit level during building renovation work.',
      must_show:['spirit level'],
      must_not_show:['laser level'],
      queries_en:[
        'construction worker using spirit level',
        'spirit level building renovation',
        'spirit level',
      ],
    }],
  });
  const $=name=>({first:()=>({json:name==='Build Narration Language Review Final'?built:promptCtx})});
  const out=new Function('$','$json',byName['Validate Narration Language Review Final'].parameters.jsCode)($,provider).json;
  const shot=out.storyboard.scenes[0].shots[0];

  assert.equal(out.storyboard.narration,source.storyboard.narration);
  assert.deepEqual(out.accepted_voiceover_candidate,source.accepted_voiceover_candidate);
  assert.equal(shot.visual_intent,'A construction worker holding a spirit level during building renovation work.');
  assert.deepEqual(shot.must_show,['spirit level']);
  assert.deepEqual(shot.must_not_show,['laser level']);
  assert.deepEqual(shot.queries_en,[
    'construction worker using spirit level',
    'spirit level building renovation',
    'spirit level',
  ]);
  assert.equal(shot.preferred_media_type,'photo');
  assert.equal(out.language_review.passed,true);
  assert.equal(out.language_review.visual_repairs.length,1);
});

test('11790 final visual repair rejects structural drift and missing repair contract',()=>{
  const built=buildFinal();
  const $=name=>({first:()=>({json:name==='Build Narration Language Review Final'?built:promptCtx})});
  const validate=data=>new Function('$','$json',byName['Validate Narration Language Review Final'].parameters.jsCode)($,data);

  assert.throws(
    ()=>validate(response({language:'pl',issues:[]})),
    /Language review contract invalid/
  );

  assert.throws(
    ()=>validate(response({
      language:'pl',
      issues:[],
      visual_repairs:[{
        scene_id:'S3',
        shot_id:'S3-A',
        visual_intent:'A spirit level with a bubble vial.',
        must_show:['spirit level','bubble vial'],
        must_not_show:['laser level'],
        queries_en:['spirit level bubble vial','spirit level construction','spirit level'],
      }],
    })),
    /structural drift/
  );
});
