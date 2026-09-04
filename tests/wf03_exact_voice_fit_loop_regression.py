import json
w=json.load(open('n8n/workflows/WF03-natural-edge-voice.json',encoding='utf-8'));w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
for x in ['Evaluate Natural Voiceover','Voiceover Fits Target','Prepare Duration Rewrite','Rewrite Narration For Exact Duration','Apply Duration Rewrite','Persist Duration Rewrite','Resume Rewritten Voiceover']:
 assert x in n
assert 'Speech-speed manipulation is forbidden' in n['Evaluate Natural Voiceover']['parameters']['jsCode']
assert 'max_fit_passes:2' in n['Prepare Continuous Voiceover']['parameters']['jsCode']
assert w['connections']['Voiceover Fits Target']['main'][1][0]['node']=='Prepare Duration Rewrite'
assert w['connections']['Resume Rewritten Voiceover']['main'][0][0]['node']=='Generate Natural Voiceover'
assert 'Do not manipulate speech rate' in n['Prepare Duration Rewrite']['parameters']['jsCode']
print('WF03_EXACT_VOICE_FIT_LOOP_REGRESSION_PASS')
