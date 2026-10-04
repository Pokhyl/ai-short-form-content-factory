const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const nodes=w.nodes.filter(n=>n.parameters.jsCode?.includes('function groundSurfaceOwnerAnchors('));
const fn=(src,name,end,ground)=>new Function('groundSurfaceOwnerAnchors',src.slice(src.indexOf('function '+name+'('),src.indexOf(end,src.indexOf('function '+name+'(')))+';return '+name)(ground);
test('all four M5 validators restore the independently visible owner from the exact S8 contract',()=>{
 assert.equal(nodes.length,4);
 for(const n of nodes){
  const src=n.parameters.jsCode;
  const ground=fn(src,'groundSurfaceOwnerAnchors','function canonicalizeTransientPhotoActionIntent(');
  const interaction=src.includes('function assertRequiredInteractionSecondary(')?fn(src,'assertRequiredInteractionSecondary','function canonicalizeHiddenPrimaryPhotoIntent(',ground):null;
  const anchors=ground(['paper sheets'],'Paper sheets showing bent staple ends on back',['bent staple ends on paper back','stapled documents back side view paper sheets','paper sheets']);
  assert.deepEqual(anchors,['paper sheets','staple']);
  if(interaction)assert.equal(interaction(anchors,'Paper sheets showing bent staple ends on back'),'staple');
  assert.match(src,/groundSurfaceOwnerAnchors\(mustShow, visualIntent, sourceQueries\)/);
 }
});
test('generic cloth/wire relation is grounded without introducing a new visual subject',()=>{
 for(const n of nodes){const ground=fn(n.parameters.jsCode,'groundSurfaceOwnerAnchors','function canonicalizeTransientPhotoActionIntent(');
  assert.deepEqual(ground(['cloth'],'Cloth showing curved wire tips on its back',['curved wire tips cloth','cloth wire fastener','cloth']),['cloth','wire']);
 }
});
test('ordinary surfaces, dependent material edges and unsupported owners remain unchanged',()=>{
 for(const n of nodes){const ground=fn(n.parameters.jsCode,'groundSurfaceOwnerAnchors','function canonicalizeTransientPhotoActionIntent(');
  for(const [anchors,intent,queries] of [
   [['paper sheets'],'Paper sheets on a desk',['paper sheets']],
   [['paper sheets'],'Paper sheets showing folded paper edges',['folded paper edges']],
   [['steel panel'],'Steel panel showing bent metal edges',['bent metal edges']],
   [['paper sheets'],'Paper sheets showing bent nail ends',['staple paper']],
   [['paper sheets','staple'],'Paper sheets showing bent staple ends',['staple paper']],
  ])assert.deepEqual(ground(anchors,intent,queries),anchors);
 }
});
test('explicit fastened result grounds its independently required connector across all validators',()=>{
 for(const n of nodes){const ground=fn(n.parameters.jsCode,'groundSurfaceOwnerAnchors','function canonicalizeTransientPhotoActionIntent(');
  assert.deepEqual(ground(['office documents'],'A neatly stapled stack of office documents',['neatly stapled stack of office documents','bound paper reports on desk office documents']),['office documents','staple']);
  assert.deepEqual(ground(['metal plates'],'A stack of bolted metal plates',['bolted metal plates joint','metal plates bolt head']),['metal plates','bolt']);
 }
});
test('final M5 canonicalization keeps required fasteners and preserves narration word for word',()=>{
 const src=w.nodes.find(n=>n.name==='Canonicalize Final Storyboard').parameters.jsCode;
 const f=JSON.parse(fs.readFileSync('tests/fixtures/m8-12040-fastened-result.json'));
 const narration='Staples keep important documents firmly joined.';
 const source={storyboard:{narration,scenes:[{scene_id:'S1',narration,shots:[{...f.shot,shot_id:'S1-A'}]}]}};
 const out=new Function('$','$json',src)(name=>({first:()=>({json:name==='Normalize Timing Probe'?source:{language_code:'en'}})}),source).json;
 assert.equal(out.storyboard.narration,narration);
 assert.deepEqual(out.storyboard.scenes[0].shots[0].must_show,['office documents','staple']);
 assert.equal(out.storyboard.scenes[0].shots[0].visual_intent,f.shot.visual_intent);
 assert.deepEqual(out.storyboard.scenes[0].shots[0].must_not_show,['person']);
 assert.match(out.storyboard.scenes[0].shots[0].queries_en[2],/staple/);
});
