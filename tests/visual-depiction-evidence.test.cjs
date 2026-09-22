const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const code=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;

function body({id=1,title,objectName=title,categories='',description='',mime='image/jpeg'}){
  return {
    query:{pages:{
      [id]:{
        pageid:id,
        index:1,
        title:'File:'+title,
        imageinfo:[{
          mime,
          url:'https://upload.wikimedia.org/wikipedia/commons/a/aa/example.jpg',
          thumburl:'https://upload.wikimedia.org/wikipedia/commons/a/aa/example.jpg',
          width:1600,height:1200,thumbwidth:1600,thumbheight:1200,size:100000,
          descriptionurl:'https://commons.wikimedia.org/wiki/File:Example.jpg',
          extmetadata:{
            LicenseShortName:{value:'Public domain'},
            ObjectName:{value:objectName},
            Categories:{value:categories},
            ImageDescription:{value:description},
          },
        }],
      },
    }},
  };
}

function normalize(ctx,b){
  const $=name=>name==='Build Wikimedia Requests'
    ? {item:{json:{visual_run_id:'run',shot_uuid:'shot',shot_key:'S1-A',scene_order:1,query_index:1,endpoint_kind:'photo',preferred_media_type:'photo',provider:'wikimedia',provider_query:ctx.query,...ctx}}}
    : (()=>{throw new Error(name)})();
  return new Function('$','$json',code('Normalize Wikimedia'))($,{statusCode:200,body:b}).json.candidates[0];
}

test('Wikimedia reservoir mentioned only as tunnel source context cannot prove depicted reservoir',()=>{
  const ctx={
    query:'hydroelectric dam reservoir water',
    visual_intent:'Hydroelectric dam reservoir holding water behind concrete barrier',
    must_show:['water reservoir','concrete dam'],
    must_not_show:[],
    domain_context_terms:[],
  };
  const c=normalize(ctx,body({
    title:'Interior of concrete-lined tunnel constructed to carry water from the Gorge Dam reservoir to the Powerhouse',
    categories:'Interiors of tunnels|Construction of Gorge Dam',
    description:'Concrete lined tunnel, 20 feet, 6 inches diameter',
  }));
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/wikimedia_primary_only_contextual_metadata/);
});

test('Wikimedia air pipe for penstocks cannot prove depicted penstock pipe',()=>{
  const ctx={
    query:'penstock pipe',
    visual_intent:'Water flowing downward through penstock pipe or waterfall spillway',
    must_show:['penstock pipe'],
    must_not_show:[],
    domain_context_terms:[],
  };
  const c=normalize(ctx,body({
    title:'Air pipe installation for penstocks next to powerhouse',
    categories:'Penstocks in the United States|White River Hydroelectric Power Plant',
    description:'Air pipes for penstocks, looking south',
  }));
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/wikimedia_primary_only_contextual_metadata/);
});

test('Wikimedia direct reservoir title proves depicted reservoir without requiring the water adjective',()=>{
  const ctx={
    query:'hydroelectric dam reservoir water',
    visual_intent:'Hydroelectric dam reservoir holding water behind concrete barrier',
    must_show:['water reservoir','concrete dam'],
    must_not_show:[],
    domain_context_terms:[],
  };
  const c=normalize(ctx,body({
    title:'Bhlaraidh Reservoir Dam',
    categories:'Reservoirs|Concrete dams',
    description:'Reservoir dam feeding a hydroelectric station',
  }));
  assert.equal(c.rejected,false,c.rejection_reason);
});

test('Wikimedia direct penstock title proves depicted penstock pipe',()=>{
  const ctx={
    query:'penstock pipe',
    visual_intent:'Large penstock pipe directing water downward in a power plant',
    must_show:['penstock pipe'],
    must_not_show:[],
    domain_context_terms:[],
  };
  const c=normalize(ctx,body({
    title:'Penstock Pipe at Angamozhi',
    categories:'Penstocks in India|Hydroelectric power',
    description:'Penstock pipe used by the hydropower project',
  }));
  assert.equal(c.rejected,false,c.rejection_reason);
});

test('unrequested turbine case view does not substitute for whole turbine subject',()=>{
  const ctx={
    query:'hydroelectric turbine mechanism',
    visual_intent:'Water turbine runner inside hydroelectric plant machinery',
    must_show:['water turbine'],
    must_not_show:[],
    domain_context_terms:['hydroelectric'],
  };
  const c=normalize(ctx,body({
    title:'TOP-VIEW OF TURBINE CASE WITH WICKET GATE MECHANISM FOR GENERATOR',
    categories:'Hydroelectric plant|Turbines',
  }));
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/wikimedia_unrequested_component_view:case/);
});

test('component view remains allowed when storyboard explicitly asks for that component',()=>{
  const ctx={
    query:'hydroelectric turbine casing',
    visual_intent:'Close view of turbine casing inside hydroelectric plant',
    must_show:['water turbine'],
    must_not_show:[],
    domain_context_terms:['hydroelectric'],
  };
  const c=normalize(ctx,body({
    title:'DETAIL OF TURBINE CASING',
    categories:'Hydroelectric plant|Turbines',
  }));
  assert.equal(c.rejected,false,c.rejection_reason);
});


test('Wikimedia primary explicitly relegated to background is rejected when another object owns foreground',()=>{
  const ctx={
    query:'hydroelectric electric generator machine',
    visual_intent:'electric generator machine inside power station',
    must_show:['electric generator'],
    must_not_show:[],
    domain_context_terms:['hydroelectric'],
  };
  const c=normalize(ctx,body({
    title:'DETAIL OF GOVERNOR STAND (FOREGROUND) AT UNIT 3 GENERATOR (BACKGROUND). VIEW TO EAST-NORTHEAST',
    categories:'Black Eagle Hydroelectric Facility|Hydroelectric power plants',
  }));
  assert.equal(c.rejected,true,c.rejection_reason);
  assert.match(c.rejection_reason,/wikimedia_primary_background_only/);
});

test('Wikimedia generator in foreground remains eligible for generator storyboard',()=>{
  const ctx={
    query:'hydroelectric electric generator machine',
    visual_intent:'electric generator machine inside power station',
    must_show:['electric generator'],
    must_not_show:[],
    domain_context_terms:['hydroelectric'],
  };
  const c=normalize(ctx,body({
    title:'Context view of powerhouse generating floor showing unit 4 generator in the foreground',
    categories:'Holter Hydroelectric Facility|Hydroelectric power plants',
  }));
  assert.equal(c.rejected,false,c.rejection_reason);
});

test('Wikimedia background primary is allowed when storyboard explicitly requests background composition',()=>{
  const ctx={
    query:'hydroelectric electric generator machine',
    visual_intent:'control equipment with electric generator in background inside power station',
    must_show:['electric generator'],
    must_not_show:[],
    domain_context_terms:['hydroelectric'],
  };
  const c=normalize(ctx,body({
    title:'DETAIL OF GOVERNOR STAND (FOREGROUND) AT UNIT 3 GENERATOR (BACKGROUND)',
    categories:'Black Eagle Hydroelectric Facility|Hydroelectric power plants',
  }));
  assert.equal(c.rejected,false,c.rejection_reason);
});
