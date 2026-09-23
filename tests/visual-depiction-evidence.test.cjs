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


test('9532 regression: concrete transformer category plus requested substation setting proves operational S5 image',()=>{
  const ctx={
    query:'high voltage electrical transformer station',
    visual_intent:'Large electrical transformer substation outdoors near power plant',
    must_show:['electrical transformer'],
    must_not_show:[],
    domain_context_terms:['substation'],
  };
  const c=normalize(ctx,body({
    id:54317267,
    title:'Electrical substation, Cosne-Cours-sur-Loire, 58-Fr (2).jpg',
    objectName:'Electrical substation, Cosne-Cours-sur-Loire, 58-Fr (2)',
    categories:'High-voltage transformers|Transformer cooling fans|Electrical substations in Cosne-Cours-sur-Loire',
    description:'Sous-station électrique, rue des Frères Lumière, Cosne-Cours-sur-Loire, France.',
  }));
  assert.equal(c.rejected,false,c.rejection_reason);
  assert.equal(c.relevance_score,100);
});

test('machinery-only category depiction relaxation does not let contextual reservoir categories prove a reservoir',()=>{
  const ctx={
    query:'water reservoir',
    visual_intent:'Large water reservoir near hydroelectric power plant',
    must_show:['water reservoir'],
    must_not_show:[],
    domain_context_terms:[],
  };
  const c=normalize(ctx,body({
    title:'Concrete tunnel portal',
    objectName:'Concrete tunnel portal',
    categories:'Reservoirs in France|Hydroelectric power plants in France',
    description:'Tunnel carrying water from a reservoir.',
  }));
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/wikimedia_primary_only_contextual_metadata/);
});


test('9552 regression: turbine-generator hall at a power station is valid operational generator evidence',()=>{
  const ctx={
    query:'electric generator machine in power plant',
    visual_intent:'large electric generator machine inside a power plant generator hall',
    must_show:['electric generator'],
    must_not_show:['solar panel','wind turbine'],
    domain_context_terms:['hall'],
  };
  const c=normalize(ctx,body({
    id:34379813,
    title:'TURBINE HALL, PERSPECTIVE VIEW OF UNIT 2 and SOUTH GALLERY BEYOND - Delaware County Electric Company, Chester Station',
    objectName:'TURBINE HALL, PERSPECTIVE VIEW OF UNIT 2 and SOUTH GALLERY BEYOND - Delaware County Electric Company, Chester Station',
    categories:'Chester Waterside Station of the Philadelphia Electric Company|Steam turbine generator sets|Turbine halls|Historic American Engineering Record images of Pennsylvania',
    description:'Turbine hall, perspective view of unit 2 and south gallery beyond.',
  }));
  assert.equal(c.rejected,false,c.rejection_reason);
});

test('generic hall does not substitute for a power-generation operational setting',()=>{
  const ctx={
    query:'electric generator machine in power plant',
    visual_intent:'large electric generator machine inside a power plant generator hall',
    must_show:['electric generator'],
    must_not_show:['solar panel','wind turbine'],
    domain_context_terms:[],
  };
  const c=normalize(ctx,body({
    id:999001,
    title:'Portable electric generator displayed in exhibition hall',
    objectName:'Portable electric generator displayed in exhibition hall',
    categories:'Portable generators|Exhibition halls',
    description:'Portable generator on display.',
  }));
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/missing_operational_setting_context/);
});

test('visual request planners treat hall as scene setting rather than hard domain',()=>{
  for(const provider of ['Pixabay','Pexels','Wikimedia']){
    const planner=code('Build '+provider+' Requests');
    assert.match(planner,/receiver room hall halls photo photograph/);
    assert.match(planner,/outdoor outdoors indoor indoors hall halls/);
  }
});


test('9229 regression: generator unit title cannot become a water turbine from contextual Turbine halls category',()=>{
  const ctx={
    query:'hydroelectric water turbine runner',
    visual_intent:'industrial water turbine runner being rotated by water flow inside hydroelectric plant',
    must_show:['water turbine'],
    must_not_show:[],
    domain_context_terms:['hydroelectric'],
  };
  const c=normalize(ctx,body({
    id:33683614,
    title:'CLOSE-UP VIEW OF A GENERATOR UNIT WITH ITS ASSOCIATED INSTRUMENTATION AND CONTROL PANEL. - Wilson Dam and Hydroelectric Plant, Turbine and Generator Unit',
    objectName:'CLOSE-UP VIEW OF A GENERATOR UNIT WITH ITS ASSOCIATED INSTRUMENTATION AND CONTROL PANEL. - Wilson Dam and Hydroelectric Plant, Turbine and Generator Unit',
    categories:'Wilson Dam|Turbine halls|Historic American Engineering Record images',
    description:'Close-up view of a generator unit and control panel.',
  }));
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/wikimedia_primary_only_contextual_metadata/);
});


test('current PL15 S5 catalog title cannot prove transformer when direct caption depicts survey equipment',()=>{
  const ctx={
    query:'power transmission lines transformer',
    visual_intent:'Power transmission lines and electrical transformer station',
    must_show:['electrical transformer'],
    must_not_show:['wind turbine','nuclear cooling tower'],
    domain_context_terms:[],
  };
  const c=normalize(ctx,body({
    id:136934049,
    title:'Contract No. 150, Installation of a Waterwheel, Generator, Switchgear, Transformer, Substation, and the Construction of a Transmission Line, Winsor Dam Power Plant, Belchertown, gen - DPLA - 4a0239e6a4d811578be7dc63cd8e7b0b.jpg',
    objectName:'Contract No. 150, Installation of a Waterwheel, Generator, Switchgear, Transformer, Substation, and the Construction of a Transmission Line, Winsor Dam Power Plant, Belchertown, gen - DPLA - 4a0239e6a4d811578be7dc63cd8e7b0b',
    categories:'Media contributed by the Digital Public Library of America|Media contributed by Massachusetts Archives|Files from the Massachusetts Water Resources Authority',
    description:'Title supplied by cataloger. Print in album volume MDWSC, Contract 150, Winsor Dam Power Plant, Installation of Equipment, Quabbin Reservoir, Volume 1, Chief Engineer set. See surveying level in foreground, center.',
  }));
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/wikimedia_primary_only_contextual_metadata/);
});

test('current PL15 S1 archival album context cannot turn reservoir construction collection text into depicted reservoir',()=>{
  const ctx={
    query:'concrete dam',
    visual_intent:'Large water reservoir behind a concrete dam',
    must_show:['water reservoir','concrete dam'],
    must_not_show:['wind turbine','dry riverbed'],
    domain_context_terms:[],
  };
  const c=normalize(ctx,body({
    id:124944982,
    title:'Wachusett Reservoir, Quinapoxet River concrete dam, Oakdale, West Boylston, Mass., Nov. 13, 1905 - DPLA - 13c16a2e721109e65ef5d33b8e6fa856.jpg',
    objectName:'Wachusett Reservoir, Quinapoxet River concrete dam, Oakdale, West Boylston, Mass., Nov. 13, 1905 - DPLA - 13c16a2e721109e65ef5d33b8e6fa856',
    categories:'Quinapoxet River|Wachusett Reservoir construction images from the Massachusetts Metropolitan Water and Sewerage Board|Photographs MWW Wachusett Reservoir construction, Vol. 10.',
    description:'Print in album Photographs MWW Wachusett Reservoir construction, Vol. 10.',
  }));
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/wikimedia_primary_only_contextual_metadata/);
});

test('archival catalog metadata still allows an explicitly depictive title or caption',()=>{
  const ctx={
    query:'hydroelectric generator turbine shaft',
    visual_intent:'Electrical generator connected to turbine shaft',
    must_show:['electric generator','turbine shaft'],
    must_not_show:[],
    domain_context_terms:['hydroelectric'],
  };
  const c=normalize(ctx,body({
    id:34522651,
    title:'DETAIL VIEW OF GENERATOR BAY, GENERATOR ROOM, SHOWING TURBINE-GENERATOR DRIVE SHAFT IN FOREGROUND - Nine Mile Hydroelectric Development',
    objectName:'DETAIL VIEW OF GENERATOR BAY, GENERATOR ROOM, SHOWING TURBINE-GENERATOR DRIVE SHAFT IN FOREGROUND',
    categories:'Hydroelectric generators|Historic American Engineering Record images',
    description:'Title supplied by cataloger. Detail view of generator bay showing turbine-generator drive shaft in foreground.',
  }));
  assert.equal(c.rejected,false,c.rejection_reason);
});
