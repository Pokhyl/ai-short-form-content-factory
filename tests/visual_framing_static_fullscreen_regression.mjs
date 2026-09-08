import assert from 'node:assert/strict';
import { buildVisualBeatFilters } from '../services/media-worker/src/visual-framing.mjs';

const photo=buildVisualBeatFilters({index:0,duration:2.5,isImage:true,isFactualGraphic:false}).join(';');
assert.match(photo,/scale=1200:2134:force_original_aspect_ratio=increase/);
assert.match(photo,/crop=1080:1920/);
assert.match(photo,/sin\(n\*0\.018/);
assert.match(photo,/cos\(n\*0\.015/);
assert.doesNotMatch(photo,/force_original_aspect_ratio=decrease/,'ordinary photo must not remain a landscape card');
assert.doesNotMatch(photo,/boxblur|overlay=/,'ordinary photo must fill the portrait canvas instead of blurred-card framing');

const graphic=buildVisualBeatFilters({index:1,duration:2.5,isImage:true,isFactualGraphic:true}).join(';');
assert.match(graphic,/scale=1080:1920:force_original_aspect_ratio=increase/);
assert.match(graphic,/boxblur=20:1/);
assert.match(graphic,/scale=1020:1840:force_original_aspect_ratio=decrease/);
assert.match(graphic,/overlay=\(W-w\)\/2:\(H-h\)\/2/);

const video=buildVisualBeatFilters({index:2,duration:2.5,isImage:false,isFactualGraphic:false}).join(';');
assert.match(video,/scale=1080:1920:force_original_aspect_ratio=increase/);
assert.match(video,/crop=1080:1920/);
console.log('VISUAL_FRAMING_PORTRAIT_PHOTO_PASS');
