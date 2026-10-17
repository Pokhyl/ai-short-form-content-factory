/* Run: node tests/studio_browser_vm.cjs factory_next/studio_web/index.html
 * Browser-like JS runtime smoke for the actual Studio inline script.
 * No network, no TTS and no browser/global history clobbering.
 */
'use strict';
const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const html=fs.readFileSync(process.argv[2]||'factory_next/studio_web/index.html','utf8');
assert.match(html,/\[hidden\]\{display:none!important\}/);
const script=html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(script,'inline script present');
const id='77963714-f8ec-4d76-aad7-f6087b4af0a2';
const values=new Map();
function element(name){
  if(values.has(name))return values.get(name);
  const elem={
    hidden:false,value:'',disabled:false,textContent:'',style:{},dataset:{},
    children:[],attributes:{},append(...items){this.children.push(...items);},
    replaceChildren(){this.children=[];},
    setAttribute(k,v){this.attributes[k]=v;},
    getAttribute(k){return this.attributes[k]??null;},
    removeAttribute(k){delete this.attributes[k];},
    querySelectorAll(){return [];},
    pause(){},load(){},
  };
  values.set(name,elem);return elem;
}
const nativeHistory={count:0,replaceState(_state,_title,url){
  this.count+=1;
  assert.equal(url.searchParams.get('request'),id);
}};
let posted=0,created=false;
const topic='галактик а андромеда';
const request={topic,language:'uk',seconds:45};
const detail={
 id,request,status:'needs_attention',next_stage:'research',
 error_type:'ValueError',machine_pass:false,video_url:null,
 source_revision:'48cf7ff0709abd87eae9a6264cdbbf0c74fec005',
 scenes:[],sources:[],script:'',voice_duration_ms:null,photo_count:0,
 completed_stages:[]
};
const fetch=async (url,opts={})=>{
  const path=String(url);
  if(opts.method==='POST'){
    posted+=1;
    assert.equal(JSON.parse(opts.body).topic,topic);
    created=true;
    return {ok:true,json:async()=>({id,status:'queued'})};
  }
  if(path.endsWith('/api/jobs')){
    return {ok:true,json:async()=>created?[{id,request,status:detail.status}]:[]};
  }
  if(path.endsWith('/api/jobs/'+id)){
    return {ok:true,json:async()=>detail};
  }
  throw Error('Unexpected API path: '+path);
};
const ctx={
  document:{getElementById:element,createElement:element},
  location:{href:'https://studio.hodor.com.pl/factory-next/',search:''},
  history:nativeHistory,console,fetch,URL,URLSearchParams,
  setTimeout:()=>0,clearTimeout:()=>{},
};
ctx.window=ctx;
vm.createContext(ctx);
vm.runInContext(script[1],ctx,{filename:'studio-inline.js'});
(async()=>{
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(ctx.history,nativeHistory,'global history must remain built-in');
 element('topic').value=topic;
 element('language').value='uk';
 element('seconds').value='45';
 let canceled=false;
 await element('request-form').onsubmit({preventDefault(){canceled=true;}});
 assert.equal(canceled,true);
 assert.equal(posted,1,'one submit means one API job; no double creation');
 assert.equal(ctx.history,nativeHistory,'submit must not shadow browser history');
 assert.equal(nativeHistory.count,1,'one selected job updates URL');
 assert.equal(element('message').hidden,true,'valid creation must not display JS error');
 assert.equal(element('result').hidden,false,'created job visible');
 assert.equal(element('failure').hidden,false,'failed stage visible');
 assert.equal(element('video').hidden,true,'no MP4 means no video player');
 assert.equal(element('placeholder').hidden,false,'placeholder visible');
 assert.equal(element('download').hidden,true,'no download without audit');
 console.log('STUDIO_BROWSER_VM_OK: submit once; browser history intact; failed job has no video');
})().catch(e=>{console.error(e);process.exitCode=1;});
