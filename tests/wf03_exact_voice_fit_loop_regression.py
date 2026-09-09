import json
w=json.load(open('n8n/workflows/WF03-natural-edge-voice.json'));w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
for x in ['Evaluate Natural Voiceover','Voiceover Fits Target','Prepare Duration Rewrite','Rewrite Narration For Exact Duration','Apply Duration Rewrite','Persist Duration Rewrite','Resume Rewritten Voiceover','Build Exact Story Unit Timings']:
 assert x in n
assert 'Speech-speed manipulation is forbidden' in n['Evaluate Natural Voiceover']['parameters']['jsCode']
assert 'story_package' in n['Prepare Continuous Voiceover']['parameters']['jsCode']
assert 'grounded_claim is authoritative and immutable' in n['Prepare Duration Rewrite']['parameters']['jsCode']
assert 'unit_word_targets' in n['Prepare Duration Rewrite']['parameters']['jsCode']
assert 'story_package=$4::jsonb' in n['Persist Duration Rewrite']['parameters']['query']
assert w['connections']['Voiceover Fits Target']['main'][0][0]['node']=='Build Exact Story Unit Timings'
assert w['connections']['Voiceover Fits Target']['main'][1][0]['node']=='Prepare Duration Rewrite'
assert w['connections']['Resume Rewritten Voiceover']['main'][0][0]['node']=='Generate Edge Fallback'
assert 'Final Narration Needs Visual Rebind' not in n
print('WF03_EXACT_VOICE_FIT_LOOP_REGRESSION_PASS')
