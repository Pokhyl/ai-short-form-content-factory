import assert from 'node:assert/strict';
import { buildVisualBeatFilters } from '../services/media-worker/src/visual-framing.mjs';

const photo = buildVisualBeatFilters({ index: 0, duration: 2.5, isImage: true, isFactualGraphic: false }).join(';');
assert.match(photo, /scale=1080:1920:force_original_aspect_ratio=increase/);
assert.match(photo, /crop=1080:1920/);
assert.doesNotMatch(photo, /1320:2350|\bt\//);

const graphic = buildVisualBeatFilters({ index: 1, duration: 2.5, isImage: true, isFactualGraphic: true }).join(';');
assert.match(graphic, /force_original_aspect_ratio=decrease/);
assert.match(graphic, /boxblur/);

console.log('VISUAL_FRAMING_STATIC_FULLSCREEN_PASS');
