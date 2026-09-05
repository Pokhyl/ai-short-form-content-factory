import json,pathlib
s=pathlib.Path('services/media-worker/src/edge-provider-budget.mjs').read_text()
assert 'Math.max(25000, Math.min(40000' in s
w=json.load(open('n8n/workflows/WF03-natural-edge-voice.json'));w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
assert 'Generate Edge Voiceover' in n
edge=n['Generate Edge Voiceover']
assert edge['parameters']['url']=='http://media-worker:3001/audio/synthesize-free-fallback'
assert edge['parameters']['options']['timeout']==95000
assert 'target_duration_seconds' in edge['parameters']['jsonBody']
assert w['connections']['Prepare Continuous Voiceover']['main'][0][0]['node']=='Generate Edge Voiceover'
assert w['connections']['Resume Rewritten Voiceover']['main'][0][0]['node']=='Generate Edge Voiceover'
assert w['connections']['Generate Edge Voiceover']['main'][0][0]['node']=='Evaluate Natural Voiceover'
assert not any(x['type']=='n8n-nodes-base.wait' for x in w['nodes'])
text=json.dumps(w)
assert 'Gemini Voiceover' not in text
assert 'google_gemini' not in text
assert 'v4-tts-gateway' not in text
worker=pathlib.Path('services/media-worker/src/server.mjs').read_text()
assert 'attempt <= 2' in worker
print('TTS_PROVIDER_BUDGET_REGRESSION_PASS')
