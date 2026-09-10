const ARCHETYPES = new Set(["flow", "merge", "split", "comparison", "layered_stack", "assembly"]);
const ENTITY_ROLES = new Set(["input", "process", "output", "layer", "subject", "result"]);
const ENTITY_SHAPES = new Set(["box", "pill", "circle"]);
const LANES = new Set(["left", "right", "center"]);
const RELATION_KINDS = new Set(["flow", "joins", "splits", "emits", "blocks", "contains", "transforms"]);
const FORBIDDEN_GEOMETRY_FIELDS = new Set(["x","y","x1","y1","x2","y2","cx","cy","r","width","height","points","translate","scale","rotate","path","d"]);

const clean=(value)=>String(value??"").replace(/\s+/gu," ").trim();
const requiredText=(value,field)=>{const out=clean(value);if(!out)throw new Error(`${field} is required`);return out;};
const phaseValue=(value,field)=>{const out=Number(value);if(!Number.isInteger(out)||out<0||out>20)throw new Error(`${field} must be an integer between 0 and 20`);return out;};

function rejectRawGeometry(value,path="spec"){
  if(Array.isArray(value)){value.forEach((child,index)=>rejectRawGeometry(child,`${path}[${index}]`));return;}
  if(!value||typeof value!=="object")return;
  for(const [key,child] of Object.entries(value)){
    if(FORBIDDEN_GEOMETRY_FIELDS.has(key))throw new Error(`${path}.${key} is raw geometry and is forbidden in high-level diagram specs`);
    rejectRawGeometry(child,`${path}.${key}`);
  }
}

export function validateDiagramSpec(input,{expectedShotId=null,allowedFactIds=null}={}){
  if(!input||typeof input!=="object"||Array.isArray(input))throw new Error("diagram spec must be an object");
  rejectRawGeometry(input);
  const shot_id=requiredText(input.shot_id??input.beat_id,"shot_id");
  if(expectedShotId!==null&&shot_id!==expectedShotId)throw new Error(`diagram spec shot mismatch: ${shot_id} != ${expectedShotId}`);
  const archetype=requiredText(input.archetype,"archetype");if(!ARCHETYPES.has(archetype))throw new Error(`invalid diagram archetype: ${archetype}`);
  const rawFacts=Array.isArray(input.grounded_fact_ids)?input.grounded_fact_ids:[];
  const grounded_fact_ids=[...new Set(rawFacts.map(clean).filter(Boolean))];
  if(!grounded_fact_ids.length)throw new Error("diagram spec grounded_fact_ids must be non-empty");
  if(allowedFactIds){const allowed=new Set([...allowedFactIds].map(clean));if(grounded_fact_ids.some((id)=>!allowed.has(id)))throw new Error("diagram spec cites fact outside shot grounding");}
  if(!Array.isArray(input.entities)||input.entities.length<2||input.entities.length>8)throw new Error("diagram entities must contain 2-8 items");
  const entities=[];const ids=new Set();
  input.entities.forEach((raw,index)=>{
    if(!raw||typeof raw!=="object"||Array.isArray(raw))throw new Error(`entities[${index+1}] must be an object`);
    const id=requiredText(raw.id,`entities[${index+1}].id`);if(ids.has(id))throw new Error(`duplicate entity id: ${id}`);ids.add(id);
    const role=requiredText(raw.role,`entities[${index+1}].role`);if(!ENTITY_ROLES.has(role))throw new Error(`invalid entity role: ${role}`);
    const shape=clean(raw.shape)||"box";if(!ENTITY_SHAPES.has(shape))throw new Error(`invalid entity shape: ${shape}`);
    const lane=clean(raw.lane)||null;if(lane!==null&&!LANES.has(lane))throw new Error(`invalid entity lane: ${lane}`);
    const order=raw.order===undefined?index:Number(raw.order);if(!Number.isInteger(order)||order<0||order>20)throw new Error(`entities[${index+1}].order is invalid`);
    entities.push({id,label:requiredText(raw.label,`entities[${index+1}].label`),role,shape,lane,order,phase:phaseValue(raw.phase??index,`entities[${index+1}].phase`)});
  });
  const rawRelations=input.relations??[];if(!Array.isArray(rawRelations)||rawRelations.length>12)throw new Error("diagram relations must be an array of at most 12 items");
  const relations=rawRelations.map((raw,index)=>{
    if(!raw||typeof raw!=="object"||Array.isArray(raw))throw new Error(`relations[${index+1}] must be an object`);
    const from=requiredText(raw.from,`relations[${index+1}].from`),to=requiredText(raw.to,`relations[${index+1}].to`);
    if(!ids.has(from)||!ids.has(to)||from===to)throw new Error(`invalid diagram relation ${from}->${to}`);
    const kind=clean(raw.kind)||"flow";if(!RELATION_KINDS.has(kind))throw new Error(`invalid relation kind: ${kind}`);
    return {from,to,kind,label:clean(raw.label)||null,phase:phaseValue(raw.phase??index+1,`relations[${index+1}].phase`)};
  });
  const roles=entities.map((e)=>e.role);
  if(archetype==="flow"&&entities.length<2)throw new Error("flow requires at least two entities");
  if(archetype==="merge"&&(roles.filter((x)=>x==="input").length<2||!roles.some((x)=>["output","result"].includes(x))))throw new Error("merge requires at least two inputs and one output/result");
  if(archetype==="split"&&(roles.filter((x)=>x==="input").length!==1||roles.filter((x)=>["output","result"].includes(x)).length<2))throw new Error("split requires one input and at least two outputs/results");
  if(archetype==="comparison"&&!(["left","right"].every((lane)=>entities.some((e)=>e.lane===lane))))throw new Error("comparison requires both lanes");
  if(archetype==="layered_stack"&&roles.filter((x)=>x==="layer").length<2)throw new Error("layered_stack requires at least two layers");
  if(archetype==="assembly"&&(roles.filter((x)=>["input","subject"].includes(x)).length<2||!roles.some((x)=>["result","output"].includes(x))))throw new Error("assembly requires at least two inputs/subjects and one result/output");
  return {shot_id,archetype,title:clean(input.title)||null,grounded_fact_ids,entities,relations};
}

const phaseRange=(phase,maxPhase,duration)=>{if(maxPhase<=0)return [0,Math.min(duration,0.55)];const usable=Math.max(0.6,duration-0.7);const start=Math.min(duration-0.25,(phase/(maxPhase+1))*usable);const end=Math.min(duration,start+Math.min(0.65,Math.max(0.3,duration*0.12)));return [Number(start.toFixed(3)),Number(end.toFixed(3))];};
const spreadX=(count)=>count<=0?[]:count===1?[360]:count===2?[180,540]:count===3?[120,360,600]:Array.from({length:count},(_,i)=>90+i*(540/(count-1)));
const wrapLabel=(label,maxChars=18)=>{const words=label.split(/\s+/u).filter(Boolean);if(!words.length)return [label];const lines=[];let current=words[0];for(const word of words.slice(1)){const next=`${current} ${word}`;if(next.length<=maxChars)current=next;else{lines.push(current);current=word;}}lines.push(current);return lines.length<=3?lines:[lines[0],lines[1],lines.slice(2).join(" ")];};

function layoutPositions(spec){
  const positions=new Map(),kind=spec.archetype,entities=spec.entities;
  if(["flow","layered_stack"].includes(kind)){const ordered=[...entities].sort((a,b)=>a.order-b.order||a.id.localeCompare(b.id)),top=280,bottom=1030,step=(bottom-top)/Math.max(1,ordered.length-1);ordered.forEach((e,i)=>positions.set(e.id,[360,top+i*step]));}
  else if(kind==="comparison"){for(const [lane,x] of [["left",190],["right",530]]){const rows=entities.filter((e)=>e.lane===lane).sort((a,b)=>a.order-b.order||a.id.localeCompare(b.id)),top=300,bottom=1000,step=(bottom-top)/Math.max(1,rows.length-1);rows.forEach((e,i)=>positions.set(e.id,[x,top+i*step]));}const center=entities.filter((e)=>e.lane==="center").sort((a,b)=>a.order-b.order||a.id.localeCompare(b.id));const centerTop=520,centerBottom=780,centerStep=(centerBottom-centerTop)/Math.max(1,center.length-1);center.forEach((e,i)=>positions.set(e.id,[360,centerTop+i*centerStep]));}
  else if(["merge","assembly"].includes(kind)){const inputs=entities.filter((e)=>["input","subject"].includes(e.role)),middle=entities.filter((e)=>e.role==="process"),outputs=entities.filter((e)=>["output","result"].includes(e.role));spreadX(inputs.length).forEach((x,i)=>positions.set(inputs[i].id,[x,340]));middle.forEach((e,i)=>positions.set(e.id,[360,620+i*150]));outputs.forEach((e,i)=>positions.set(e.id,[360,980+i*130]));}
  else if(kind==="split"){const inputs=entities.filter((e)=>e.role==="input"),middle=entities.filter((e)=>e.role==="process"),outputs=entities.filter((e)=>["output","result"].includes(e.role));positions.set(inputs[0].id,[360,300]);middle.forEach((e,i)=>positions.set(e.id,[360,540+i*150]));spreadX(outputs.length).forEach((x,i)=>positions.set(outputs[i].id,[x,960]));}
  return positions;
}

function boxElements(entity,x,y,enter){
  const shape=entity.shape;
  const base=shape==="circle"?{id:`${entity.id}-shape`,type:"circle",cx:x,cy:y,r:66,fill:"#152238",stroke:"#75D7FF",strokeWidth:4,enter,from:{scale:0.72,opacity:0}}:{id:`${entity.id}-shape`,type:"rect",x:x-120,y:y-59,width:240,height:118,rx:shape==="pill"?58:18,fill:"#152238",stroke:"#75D7FF",strokeWidth:4,enter,from:{scale:0.86,opacity:0}};
  const lines=wrapLabel(entity.label),fontSize=lines.length>1?25:28,gap=fontSize+5,firstY=y-((lines.length-1)*gap)/2+9;
  return [base,...lines.map((text,index)=>({id:`${entity.id}-label-${index}`,type:"text",x,y:firstY+index*gap,text,fontSize,fontWeight:700,fill:"#F7FAFC",enter,from:{opacity:0}}))];
}

export function compileDiagramSpec(input,durationSeconds,options={}){
  const duration=Number(durationSeconds);if(!Number.isFinite(duration)||duration<=0)throw new Error("durationSeconds must be positive");
  const spec=validateDiagramSpec(input,options),positions=layoutPositions(spec),phases=[...spec.entities.map((e)=>e.phase),...spec.relations.map((r)=>r.phase)],maxPhase=Math.max(0,...phases),elements=[];
  for(const entity of spec.entities){const [x,y]=positions.get(entity.id);elements.push(...boxElements(entity,x,y,phaseRange(entity.phase,maxPhase,duration)));}
  spec.relations.forEach((relation,index)=>{const [sx,sy]=positions.get(relation.from),[tx,ty]=positions.get(relation.to),draw=phaseRange(relation.phase,maxPhase,duration);elements.push({id:`relation-${index+1}-${relation.from}-${relation.to}`,type:"line",x1:sx,y1:sy+58,x2:tx,y2:ty-58,stroke:"#FFB454",strokeWidth:6,arrow:true,draw});if(relation.label)elements.push({id:`relation-${index+1}-label`,type:"text",x:(sx+tx)/2,y:(sy+ty)/2-16,text:relation.label,fontSize:22,fontWeight:600,fill:"#FFDBA8",enter:draw,from:{opacity:0}});});
  return {durationSeconds:Number(duration.toFixed(3)),background:"#08111F",title:spec.title,elements,source:{shot_id:spec.shot_id,archetype:spec.archetype,compiler:"diagram-compiler-v1",grounded_fact_ids:spec.grounded_fact_ids}};
}
