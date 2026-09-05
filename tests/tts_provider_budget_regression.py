import json,pathlib
s=pathlib.Path('services/media-worker/src/edge-provider-budget.mjs').read_text()
assert 'Math.max(120000, Math.min(240000' in s
w=json.load(open('n8n/workflows/WF03-natural-edge-voice.json'));w=w[0] if isinstance(w,list) else w
g=[x for x in w['nodes'] if x['name']=='Generate Gemini Voiceover']
assert len(g)==1 and g[0]['parameters']['options']['timeout']==180000
fallback=[x for x in w['nodes'] if x['name']=='Generate Edge Fallback']
assert len(fallback)==1 and fallback[0]['parameters']['options']['timeout']==270000
assert not any('sleep' in x['name'].lower() or 'retry' in x['name'].lower() for x in w['nodes'])
print('TTS_PROVIDER_BUDGET_REGRESSION_PASS')
