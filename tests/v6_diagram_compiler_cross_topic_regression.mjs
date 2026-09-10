import assert from 'node:assert/strict';
import fs from 'node:fs';
import {compileDiagramSpec,validateDiagramSpec} from '../services/media-worker/src/diagram-compiler.mjs';
const fixture=JSON.parse(fs.readFileSync('prototype/v4/fixtures/cross_topic_graphic_specs_20260903.json','utf8'));
let compiled=0;
for(const [topic,specs] of Object.entries(fixture)){
  for(const [legacyId,legacy] of Object.entries(specs)){
    const shotId=`${topic}-${legacyId}`;
    const spec={...legacy,shot_id:shotId,grounded_fact_ids:[`F-${legacyId}`]};
    delete spec.beat_id;
    const valid=validateDiagramSpec(spec,{expectedShotId:shotId,allowedFactIds:[`F-${legacyId}`]});
    assert.equal(valid.shot_id,shotId);
    const graphic=compileDiagramSpec(spec,4,{expectedShotId:shotId,allowedFactIds:[`F-${legacyId}`]});
    assert.equal(graphic.source.compiler,'diagram-compiler-v1');
    assert.equal(graphic.source.shot_id,shotId);
    assert.ok(graphic.elements.length>=valid.entities.length*2);
    compiled++;
  }
}
assert.equal(compiled,16);
assert.throws(()=>validateDiagramSpec({shot_id:'S1',grounded_fact_ids:['F1'],archetype:'flow',entities:[{id:'a',label:'A',role:'input',x:10},{id:'b',label:'B',role:'output'}],relations:[]}),/raw geometry/);
assert.throws(()=>validateDiagramSpec({shot_id:'S1',grounded_fact_ids:['F2'],archetype:'flow',entities:[{id:'a',label:'A',role:'input'},{id:'b',label:'B',role:'output'}],relations:[]},{allowedFactIds:['F1']}),/outside shot grounding/);
const sharedMediator={shot_id:'CMP-CENTER',grounded_fact_ids:['F1'],archetype:'comparison',title:'Comparison',entities:[
  {id:'left-in',label:'Blue light',role:'input',lane:'left',order:1,phase:0},
  {id:'right-in',label:'Red light',role:'input',lane:'right',order:1,phase:0},
  {id:'molecules',label:'Air molecules',role:'subject',shape:'circle',lane:'center',order:2,phase:1},
  {id:'left-out',label:'More scattering',role:'output',lane:'left',order:3,phase:2},
  {id:'right-out',label:'Less scattering',role:'output',lane:'right',order:3,phase:2}
],relations:[
  {from:'left-in',to:'molecules',kind:'flow',phase:1},{from:'molecules',to:'left-out',kind:'emits',phase:2},
  {from:'right-in',to:'molecules',kind:'flow',phase:1},{from:'molecules',to:'right-out',kind:'flow',phase:2}
]};
const centerGraphic=compileDiagramSpec(sharedMediator,4,{expectedShotId:'CMP-CENTER',allowedFactIds:['F1']});
assert.ok(centerGraphic.elements.some(e=>e.id==='molecules-shape'),'comparison center mediator must be positioned and rendered');
console.log('V6_DIAGRAM_COMPARISON_CENTER_PASS');
console.log(`V6_DIAGRAM_COMPILER_CROSS_TOPIC_PASS ${compiled}`);
