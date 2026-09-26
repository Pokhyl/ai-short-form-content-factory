const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const code=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;

const shot={
  shot_uuid:'77777777-7777-4777-8777-777777777777',
  shot_key:'S7-A',
  scene_order:7,
  preferred_media_type:'photo',
  visual_intent:'An open aneroid barometer revealing the internal corrugated metal box.',
  must_show:['aneroid barometer','metal box'],
  must_not_show:['liquid mercury'],
  queries_en:[
    'aneroid barometer internal metal capsule',
    'corrugated metal box barometer mechanism',
    'metal box',
  ],
};

function requests(provider){
  return new Function('$',code('Build '+provider+' Requests'))(
    ()=>({first:()=>({json:{visual_run_id:'run',shots_json:[shot]}})})
  ).map(x=>x.json);
}

function commonsBody({title,objectName=title,description='',categories='Aneroid barometers'}){
  return {
    query:{pages:{1:{
      pageid:1,index:1,title:'File:'+title,
      imageinfo:[{
        mime:'image/jpeg',
        url:'https://upload.wikimedia.org/example.jpg',
        thumburl:'https://upload.wikimedia.org/example.jpg',
        width:3172,height:2379,thumbwidth:1600,thumbheight:1200,size:3766167,
        descriptionurl:'https://commons.wikimedia.org/wiki/File:Example.jpg',
        extmetadata:{
          LicenseShortName:{value:'CC BY-SA 3.0'},
          LicenseUrl:{value:'https://creativecommons.org/licenses/by-sa/3.0/'},
          ObjectName:{value:objectName},
          Categories:{value:categories},
          ImageDescription:{value:description},
        },
      }],
    }}},
  };
}

function normalize(ctx,body){
  const $=name=>{
    assert.equal(name,'Build Wikimedia Requests');
    return {item:{json:ctx}};
  };
  return new Function('$','$json',code('Normalize Wikimedia'))(
    $,{statusCode:200,body}
  ).json.candidates[0];
}

test('Commons final secondary fallback searches the primary subject broadly without weakening must_show',()=>{
  const wiki=requests('Wikimedia');
  const final=wiki.find(r=>r.query_index===3);
  assert.equal(final.query,'metal box');
  assert.equal(final.provider_query,'aneroid barometer');
  assert.deepEqual(final.must_show,['aneroid barometer','metal box']);

  const pexels=requests('Pexels').find(r=>r.query_index===3);
  const pixabay=requests('Pixabay').find(r=>r.query_index===3);
  assert.equal(pexels.provider_query,'aneroid barometer metal box');
  assert.equal(pixabay.provider_query,'aneroid barometer metal box');

  const search=workflow.nodes.find(n=>n.name==='Wikimedia Search');
  const limit=search.parameters.queryParameters.parameters.find(x=>x.name==='gsrlimit');
  assert.equal(limit.value,'20');
});

test('Commons internal-mechanism photo may reach Gemini when primary is proven but lay secondary wording is absent from metadata',()=>{
  const ctx=requests('Wikimedia').find(r=>r.query_index===3);
  const candidate=normalize(ctx,commonsBody({
    title:'Design of aneroid barometer aneroid cell.JPG',
    objectName:'Design of aneroid barometer aneroid cell',
    description:'Mechanical design of an aneroid barometer by Feingerätebau Fischer/GDR',
    categories:'Aneroid barometers|Self-published work',
  }));
  assert.equal(candidate.rejected,false,candidate.rejection_reason);
  assert.doesNotMatch(String(candidate.rejection_reason||''),/missing_secondary_subject_context/);
});

test('Commons ordinary exterior primary-subject photo still fails the secondary internal-component prefilter',()=>{
  const ctx=requests('Wikimedia').find(r=>r.query_index===3);
  const candidate=normalize(ctx,commonsBody({
    title:'Modern Aneroid Barometer.jpg',
    objectName:'Modern Aneroid Barometer',
    description:'Modern aneroid barometer',
    categories:'Aneroid barometers|Self-published work',
  }));
  assert.equal(candidate.rejected,true);
  assert.match(candidate.rejection_reason,/missing_secondary_subject_context/);
});
