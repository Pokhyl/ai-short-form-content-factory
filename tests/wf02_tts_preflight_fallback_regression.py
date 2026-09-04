import json
from pathlib import Path
w=json.loads(Path('n8n/workflows/WF02-plan-script-and-scenes.json').read_text())
w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
final=n['Build Final Grounded Script']['parameters']['jsCode']
persist=n['Persist Grounded AI Narration']['parameters']['query']
assert 'prediction_is_advisory:true' in final
assert 'exact_tts_required:true' in final
assert 'safe_for_single_tts' not in final
assert "duration_preflight->>'exact_tts_required'" in persist
assert "duration_preflight->>'prediction_is_advisory'" in persist
print('WF02_TTS_PREFLIGHT_FALLBACK_REGRESSION_PASS')
