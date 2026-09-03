import assert from 'node:assert/strict';
import { evaluateVisualShotSequence, requiredRenderedShotStateCount } from '../services/media-worker/src/visual-quality.mjs';

const shots=[];
let t=0;
for(let i=0;i<10;i++){
  const d=4.0, cluster=`c${i}`;
  shots.push({shot_number:i+1,start_seconds:t,end_seconds:t+d,duration_seconds:d,asset_key:`asset-${i+1}`,visual_cluster_key:cluster});
  t+=d;
}
const q=evaluateVisualShotSequence(shots);
assert.equal(q.version,'visual-segments-v3');
assert.equal(q.shot_count,10);
assert.equal(q.all_assets_unique,true);
assert.equal(q.asset_reuse_count,0);
assert.equal(q.adjacent_visual_cluster_duplicate_count,0);
assert.equal(q.pass,true);
assert.equal(requiredRenderedShotStateCount(9),5);

const adjacent=evaluateVisualShotSequence([
  {shot_number:1,start_seconds:0,end_seconds:2,duration_seconds:2,asset_key:'a',visual_cluster_key:'x'},
  {shot_number:2,start_seconds:2,end_seconds:4,duration_seconds:2,asset_key:'b',visual_cluster_key:'x'},
  {shot_number:3,start_seconds:4,end_seconds:6,duration_seconds:2,asset_key:'c',visual_cluster_key:'z'},
]);
assert.equal(adjacent.pass,false);
assert.equal(adjacent.adjacent_visual_cluster_duplicate_count,1);

const longSemanticShots=evaluateVisualShotSequence([
  {shot_number:1,start_seconds:0,end_seconds:6,duration_seconds:6,asset_key:'a',visual_cluster_key:'x'},
  {shot_number:2,start_seconds:6,end_seconds:12,duration_seconds:6,asset_key:'b',visual_cluster_key:'y'},
  {shot_number:3,start_seconds:12,end_seconds:18,duration_seconds:6,asset_key:'c',visual_cluster_key:'z'},
]);
assert.equal(longSemanticShots.pass,true,'a shot longer than five seconds is valid when semantic timing and video-level diversity remain valid');
assert.equal(longSemanticShots.max_shot_duration_seconds,6);

const repeatedAsset=evaluateVisualShotSequence([
  {shot_number:1,start_seconds:0,end_seconds:1,duration_seconds:1,asset_key:'same',visual_cluster_key:'x'},
  {shot_number:2,start_seconds:1,end_seconds:2,duration_seconds:1,asset_key:'b',visual_cluster_key:'y'},
  {shot_number:3,start_seconds:2,end_seconds:3,duration_seconds:1,asset_key:'same',visual_cluster_key:'x'},
  {shot_number:4,start_seconds:3,end_seconds:4,duration_seconds:1,asset_key:'d',visual_cluster_key:'z'},
  {shot_number:5,start_seconds:4,end_seconds:5,duration_seconds:1,asset_key:'e',visual_cluster_key:'w'},
  {shot_number:6,start_seconds:5,end_seconds:6,duration_seconds:1,asset_key:'f',visual_cluster_key:'v'},
]);
assert.equal(repeatedAsset.pass,true,'non-adjacent asset reuse may pass when perceptual occurrence and duration-share gates pass');
assert.equal(repeatedAsset.all_assets_unique,false);
assert.equal(repeatedAsset.asset_reuse_count,1);
assert.equal(repeatedAsset.max_visual_cluster_duration_share,0.3333);
console.log(JSON.stringify({pass:true,quality:q,reused_asset_quality:repeatedAsset}));
