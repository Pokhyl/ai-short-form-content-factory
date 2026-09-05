import json
from pathlib import Path
w=json.load(open('n8n/workflows/WF03-natural-edge-voice.json',encoding='utf-8'));w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
for x in ['Evaluate Natural Voiceover','Voiceover Fits Target','Prepare Duration Rewrite','Rewrite Narration For Exact Duration','Apply Duration Rewrite','Persist Duration Rewrite','Resume Rewritten Voiceover','Generate Edge Voiceover']:
 assert x in n
assert 'Speech-speed manipulation is forbidden' in n['Evaluate Natural Voiceover']['parameters']['jsCode']
assert "Resume Rewritten Voiceover').all().at(-1)" in n['Evaluate Natural Voiceover']['parameters']['jsCode']
assert "Prepare Duration Rewrite').first().json?.retry_context" not in n['Evaluate Natural Voiceover']['parameters']['jsCode']
assert 'edge_fallback_voice' not in n['Apply Duration Rewrite']['parameters']['jsCode']
assert 'max_fit_passes:3' in n['Prepare Continuous Voiceover']['parameters']['jsCode']
assert "provider:'microsoft_edge_readaloud'" in n['Prepare Continuous Voiceover']['parameters']['jsCode']
assert "model:'edge_neural'" in n['Prepare Continuous Voiceover']['parameters']['jsCode']
assert 'script_fit_passes <= 3' in Path('db/migrations/021_expand_script_fit_pass_limit_to_three.sql').read_text()
assert w['connections']['Voiceover Fits Target']['main'][1][0]['node']=='Prepare Duration Rewrite'
assert w['connections']['Resume Rewritten Voiceover']['main'][0][0]['node']=='Generate Edge Voiceover'
assert w['connections']['Prepare Continuous Voiceover']['main'][0][0]['node']=='Generate Edge Voiceover'
assert 'Do not manipulate speech rate' in n['Prepare Duration Rewrite']['parameters']['jsCode']
assert 'measured_bracket_interpolation' in n['Prepare Duration Rewrite']['parameters']['jsCode']
assert 'fit_history' in n['Evaluate Natural Voiceover']['parameters']['jsCode']
assert 'google_gemini' not in json.dumps(w)
print('WF03_EXACT_VOICE_FIT_LOOP_REGRESSION_PASS')
