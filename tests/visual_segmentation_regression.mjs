import assert from 'node:assert/strict';
import { buildVisualSegments } from '../services/media-worker/src/visual-segmentation.mjs';

function beatsFromDurations(durations, narrations, supports) {
  let t=0;
  return durations.map((duration,index)=>{
    const start=t; t+=duration;
    return {scene_number:index+1,beat_start_seconds:start,beat_end_seconds:t,duration_seconds:duration,narration:narrations[index],narration_support_evidence_ids:supports[index]};
  });
}

const ukDur=[3.264,2.845,2.95,2.705,3.526,3.194,2.88,2.967,3.177,4.102,3.404,3.735,3.596,3.316,3.421,3.456,2.461,2.217];
const ukText=[
'Індукці́йна плита́ — кухонна електрична плита,','що розігріває металевий посуд індукованими','вихровими струмами, що генеруються високочастотним','магнітним полем частотою 20-100 кГц.','Але нижче, ніж до приблизно 20 кГц,','частоти не знижують, щоб уникнути появи','некомфортного для користувачів звуку (частоти','вище 20 кГц люди не чують).','Тому при виборі потужності нижче тієї,','при якій інвертор працює на частоті 20 кГц,','конфорка переходить в режим переривчастого нагріву:','раз на кілька секунд вмикається і вимикається.','Чим на менший час вона буде вмикатися,','тим меншою буде потужність. Також випускаються','плити з комбінованим набором нагрівальних елементів:','частина конфорок індукційні, частина використовує ТЕНи.','Регулювання потужності здійснюється, зазвичай,','двояко: безперервно і імпульсно.'
];
const support=ukText.map((_,i)=> i<4?['E1']:i<8?['E2']:i<12?['E3']:i<16?['E4']:['E5']);
const uk=buildVisualSegments(beatsFromDurations(ukDur,ukText,support));
assert.equal(uk.duration_seconds,57.216);
assert.equal(uk.version,'semantic-visual-segments-v3');
assert.ok(uk.segment_count < 18,'57s fixture must not create one visual search per timed beat');
assert.ok(uk.segment_count >= 7 && uk.segment_count <= 13,`unexpected UK segment count ${uk.segment_count}`);
assert.equal(uk.segments[0].start_seconds,0);
assert.equal(uk.segments.at(-1).end_seconds,57.216);
for(let i=0;i<uk.segments.length;i++){
 const s=uk.segments[i];
 assert.equal(s.segment_number,i+1);
 assert.ok(s.duration_seconds<=Math.min(8.5,uk.duration_seconds*0.34)+0.02);
 assert.equal(s.planned_shot_count,s.duration_seconds>=1.8?2:1,'every readable segment must use two distinct stills');
 if(i) assert.ok(Math.abs(s.start_seconds-uk.segments[i-1].end_seconds)<=0.012);
 assert.ok(s.support_evidence_ids.length>0);
}
const shotCount=uk.segments.reduce((n,s)=>n+s.planned_shot_count,0);
assert.ok(shotCount>uk.segment_count,'normal-length semantic segments must contain more than one still');

const zipperDur=[2.620,2.926,2.633,2.722,2.328,2.251];
const zipperText=[
 'A zipper consists of a slider mounted','on two rows of metal or plastic teeth.',
 'The slider, operated by hand, contains a','Y-shaped channel that meshes or separates them.',
 'The teeth may be individually discrete','or shaped from a continuous coil.'
];
const zipperSupport=[['W1:P3:S1'],['W1:P3:S1'],['W1:P3:S2'],['W1:P3:S2'],['W1:P3:S3'],['W1:P3:S3']];
const zipper=buildVisualSegments(beatsFromDurations(zipperDur,zipperText,zipperSupport));
const zipperCap=zipper.duration_seconds*0.34;
assert.equal(zipper.duration_seconds,15.48);
assert.ok(zipper.segment_count>3,'quality-constrained segmentation must split semantic groups that would mathematically violate the unchanged 0.34 duration-share gate');
assert.ok(zipper.segment_count<zipperDur.length,'quality-constrained segmentation must not degenerate into one search obligation per timed beat when a legal semantic grouping exists');
assert.ok(zipper.segments.every(s=>s.duration_seconds<=zipperCap+0.02),`zipper segment exceeds 0.34 cap ${zipperCap}`);
assert.ok(zipper.segments.every(s=>s.planned_shot_count===(s.duration_seconds>=1.8?2:1)));

const d=[2.5,2.5,2.5,2.5,2.5,2.5];
const sameSupport=Array.from({length:6},()=>['A']);
const punctuationRich=buildVisualSegments(beatsFromDurations(d,['Alpha mechanism.','Beta detail.','Gamma motion.','Delta result.','Epsilon context.','Zeta finish.'],sameSupport));
const continuous=buildVisualSegments(beatsFromDurations(d,['Alpha mechanism,','beta detail and','gamma motion while','delta result remains','epsilon context until','zeta finish.'],sameSupport));
assert.notEqual(punctuationRich.segment_count,continuous.segment_count,'same duration must not force a fixed visual segment count');

for(const fixture of [punctuationRich,continuous]){
 let cursor=0;
 for(const s of fixture.segments){assert.ok(Math.abs(s.start_seconds-cursor)<=0.012);cursor=s.end_seconds;}
 assert.ok(Math.abs(cursor-15)<=0.012);
}
console.log(JSON.stringify({pass:true,uk_segments:uk.segment_count,uk_shots:shotCount,zipper_segments:zipper.segment_count,zipper_cap:Number(zipperCap.toFixed(4)),punctuation_segments:punctuationRich.segment_count,continuous_segments:continuous.segment_count}));
