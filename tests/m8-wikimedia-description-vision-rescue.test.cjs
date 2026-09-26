const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const code=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;

const shot={
  shot_uuid:'33333333-3333-4333-8333-333333333333',
  shot_key:'S3-A',
  scene_order:3,
  preferred_media_type:'photo',
  visual_intent:'A barometer glass tube filled with liquid mercury.',
  must_show:['glass tube'],
  must_not_show:['digital display','plastic bottle'],
  queries_en:['glass tube barometer','mercury glass tube','glass tube'],
};

function requests(){
  return new Function('$',code('Build Wikimedia Requests'))(
    ()=>({first:()=>({json:{visual_run_id:'run',shots_json:[shot]}})})
  ).map(x=>x.json);
}

function body({title,objectName=title,description,categories}){
  return {query:{pages:{1:{
    pageid:1,index:1,title:'File:'+title,
    imageinfo:[{
      mime:'image/jpeg',
      url:'https://upload.wikimedia.org/example.jpg',
      thumburl:'https://upload.wikimedia.org/example.jpg',
      width:950,height:1800,thumbwidth:844,thumbheight:1600,size:100000,
      descriptionurl:'https://commons.wikimedia.org/wiki/File:Example.jpg',
      extmetadata:{
        LicenseShortName:{value:'CC BY-SA 4.0'},
        LicenseUrl:{value:'https://creativecommons.org/licenses/by-sa/4.0/'},
        ObjectName:{value:objectName},
        Categories:{value:categories},
        ImageDescription:{value:description},
      },
    }],
  }}}};
}

function normalize(ctx,b){
  const $=name=>{
    assert.equal(name,'Build Wikimedia Requests');
    return {item:{json:ctx}};
  };
  return new Function('$','$json',code('Normalize Wikimedia'))(
    $,{statusCode:200,body:b}
  ).json.candidates[0];
}

const longDescription=
  "Historic mercury barometer, heirloom from Germany, 19th century. "+
  "Top scale states Barometer and artisan name. The lower casing is raised "+
  "to enable view of the mercury receptacle and wooden stopper at the "+
  "upturned end of the glass tube. Height without hook is 950 mm.";

test('current S3 Commons barometer photo may reach Gemini when long description names the component and strong metadata proves the domain',()=>{
  const ctx=requests()[0];
  assert.deepEqual(ctx.domain_context_terms,['barometer']);
  const c=normalize(ctx,body({
    title:'Mercury barometer - Pariser Maasz - Germany - 19th century.jpg',
    objectName:'Mercury barometer - Pariser Maasz - Germany - 19th century',
    description:longDescription,
    categories:'Mercury barometers|Self-published work|Objects on gray background',
  }));
  assert.equal(c.rejected,true,'metadata should not directly accept component depiction');
  assert.match(c.rejection_reason,/missing_primary_subject_anchor:glass tube/);
  assert.doesNotMatch(c.rejection_reason,/wikimedia_primary_only_contextual_metadata/);
  assert.ok(c.relevance_score>=55);
});

test('long description cannot bypass contextual hard reject when strong metadata does not prove storyboard domain',()=>{
  const ctx=requests()[0];
  const c=normalize(ctx,body({
    title:'Laboratory apparatus.jpg',
    objectName:'Laboratory apparatus',
    description:longDescription,
    categories:'Laboratory equipment|Glassware',
  }));
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/wikimedia_primary_only_contextual_metadata/);
});
