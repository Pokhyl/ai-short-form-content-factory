from __future__ import annotations
import importlib.util
from pathlib import Path
path=Path('services/media-worker/python/piper_whisper_fallback.py')
spec=importlib.util.spec_from_file_location('piper_whisper_fallback',path)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def w(s,e,t): return {'start':s,'end':e,'word':t}
out=mod.align_script_to_audio_words('Шлюз поднимает судно.',[w(0,.3,'Шлюз'),w(.31,.8,'поднимает'),w(.81,1.2,'судно.')])
assert ' '.join(x['text'] for x in out)=='Шлюз поднимает судно.'
assert out[0]['start_seconds']==0 and out[-1]['end_seconds']==1.2
out=mod.align_script_to_audio_words('je nitami.',[w(0,.7,'jenitami.')])
assert [x['text'] for x in out]==['je nitami.'] and out[0]['end_seconds']==.7
try: mod.align_script_to_audio_words('Шлюз поднимает судно.',[w(.4,.9,'поднимает'),w(.91,1.2,'судно.')])
except ValueError: pass
else: raise AssertionError('missing canonical speech must fail closed instead of inventing time')
source=path.read_text()
for required in ['piper-tts-1.2.0','faster-whisper-1.2.1-cpu-int8','initial_prompt=narration','compute_type="int8"']: assert required in source
print('PIPER_WHISPER_FALLBACK_ALIGNMENT_REGRESSION_PASS')
