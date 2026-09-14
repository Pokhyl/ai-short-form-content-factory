const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const EventEmitter = require('node:events');
const {api} = require('./fixtures/api.cjs');
const fixture = require('./fixtures/scenes.cjs');

function rendererHarness(resolver, narration) {
  const events=[], exports={};
  let id=0;
  const files={createWriteStream:()=>new EventEmitter(),unlink(){},removeSync(){},writeJson:async()=>{},existsSync:()=>false};
  // Downloads and FFmpeg are isolated here; successful production planning,
  // one-shot synthesis, caption mapping and Remotion payload remain unmodified.
  files.createWriteStream=()=>{const file=new EventEmitter(); file.close=fn=>fn?.(); file.destroy=()=>{}; return file;};
  const https={get:(_url,_options,callback)=>{const request=new EventEmitter(); queueMicrotask(()=>callback({statusCode:200,pipe:file=>queueMicrotask(()=>file.emit('finish'))}));return request;}};
  const childProcess={spawn:()=>{const child=new EventEmitter();child.stderr=new EventEmitter();queueMicrotask(()=>child.emit('close',0));return child;}};
  const modules={'fs-extra':files,cuid:()=>`test-${++id}`,'https':https,'child_process':childProcess,'../logger':{logger:{debug(){},warn(){},error(){}}},'./../types/shorts':{OrientationEnum:{portrait:'portrait'}}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../engine-overlay/ShortCreator'),'utf8'),{exports,require:name=>modules[name]||require(name),Buffer,URL,console,setTimeout,clearTimeout});
  const wrapped={prepareScenes:s=>resolver.prepareScenes(s),preflightScenes:async s=>{events.push('preflight');return resolver.preflightScenes(s);},planShots:(...args)=>resolver.planShots(...args)};
  const creator=new exports.ShortCreator({tempDirPath:'/tmp',videosDirPath:'/tmp',port:3123},{render:async payload=>{events.push('render');creator.payload=payload;}},{generate:async(...args)=>{events.push('tts');creator.ttsArgs=args;return narration;}},{CreateCaption:async()=>{throw Error('Unexpected Whisper');}},{saveToMp3:async()=>{}},wrapped,{});
  creator.findMusic=()=>({url:'music',start:0,end:20});
  return {creator,events};
}
test('failed preflight prevents BOTH TTS and render', async()=>{
  const resolver=api(), {creator,events}=rendererHarness(resolver,{});
  await assert.rejects(creator.createShort('new-test',[{...fixture.scenes('en')[0],text:'Unresolvable subject.'}],{}),/unresolved_subject/);
  assert.deepEqual(events,['preflight']);
});
test('preflight precedes one synthesis; semantic scenes use different visual URLs', async()=>{
  const inputs=[{...fixture.scenes('en')[0],text:'Solar wind carries plasma. The asteroid belt contains rocks.'}];
  const text=inputs[0].text, tokens=text.split(' ');
  const narration={audioLength:6,audio:new ArrayBuffer(1),captions:tokens.map((text,i)=>({text,startMs:i*500,endMs:(i+1)*500}))};
  const {creator,events}=rendererHarness(api(),narration);
  await creator.createShort('new-test',inputs,{voice:'gemini:Enceladus'});
  assert.deepEqual(events,['preflight','tts','render']);
  assert.equal(creator.ttsArgs[0],text);
  assert.equal(creator.ttsArgs[1],'gemini:Enceladus');
  assert.equal(creator.payload.scenes.length,2);
  assert.notEqual(creator.payload.scenes[0].video,creator.payload.scenes[1].video);
  assert.equal(creator.payload.scenes.reduce((sum,s)=>sum+s.audio.duration,0),6);
  assert.ok(creator.payload.scenes.every(s=>s.visuals.length===1));
});
test('duration gate still rejects synthesis outside the existing tolerance',async()=>{
  const {creator,events}=rendererHarness(api(),{audioLength:20});
  await assert.rejects(creator.createShort('new-test',[{...fixture.scenes('en')[0],text:'Solar wind carries plasma.'}],{targetDurationSeconds:15}),/outside target/);
  assert.deepEqual(events,['preflight','tts']);
});
test('20 second scenes switch exact visuals at intervals no longer than eight seconds',async()=>{
  const resolver=api();
  resolver.commonsMedia=async()=>[{id:'alternative',mediaKey:'alternative.jpg',source:'exact_entity_commons',kind:'image',url:'https://upload.wikimedia.org/a.jpg'}];
  const [media]=await resolver.preflightScenes([{...fixture.scenes('en')[0],text:'Solar wind carries plasma.'}]);
  const shots=await resolver.planShots(media,20);
  assert.equal(shots.length,3);
  assert.ok(shots.every(s=>s.durationSeconds<=8));
  assert.notEqual(shots[0].media.mediaKey,shots[1].media.mediaKey);
  assert.equal(shots.reduce((sum,s)=>sum+s.durationSeconds,0),20);
});
test('long hold is permitted only with recorded absence of any exact alternative',async()=>{
  const resolver=api();
  const [media]=await resolver.preflightScenes([{...fixture.scenes('en')[0],text:'Solar wind carries plasma.'}]);
  const shots=await resolver.planShots(media,20);
  assert.equal(shots.length,1);
  assert.equal(shots[0].holdReason,'same_entity_no_alternative');
});
test('raw unverified media cannot enter the timed shot planner',async()=>{
  await assert.rejects(api().planShots({groundedEntity:'Solar wind'},20),/invalid_visual_plan/);
});
