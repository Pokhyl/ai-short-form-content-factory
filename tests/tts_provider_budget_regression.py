import json,pathlib
s=pathlib.Path('services/media-worker/src/edge-provider-budget.mjs').read_text()
assert 'Math.max(120000, Math.min(240000' in s
w=json.load(open('n8n/workflows/WF03-natural-edge-voice.json'));w=w[0] if isinstance(w,list) else w
g=[x for x in w['nodes'] if x['name']=='Generate Gemini Voiceover']
assert len(g)==1 and g[0]['parameters']['options']['timeout']==180000
assert not g[0].get('retryOnFail')
wait=[x for x in w['nodes'] if x['name']=='Wait Once For TTS Quota']
assert len(wait)==1 and wait[0]['parameters']=={'resume':'timeInterval','amount':60,'unit':'seconds'}
retry=[x for x in w['nodes'] if x['name']=='Retry Gemini Voiceover Once']
assert len(retry)==1
assert w['connections']['Generate Gemini Voiceover']['main'][1][0]['node']=='Prepare Gemini TTS Retry'
assert w['connections']['Prepare Gemini TTS Retry']['main'][0][0]['node']=='Wait Once For TTS Quota'
assert "Resume Rewritten Voiceover').all().at(-1)" in next(x for x in w['nodes'] if x['name']=='Prepare Gemini TTS Retry')['parameters']['jsCode']
assert w['connections']['Retry Gemini Voiceover Once']['main'][1][0]['node']=='Prepare Edge Fallback'
fallback=[x for x in w['nodes'] if x['name']=='Generate Edge Fallback']
assert len(fallback)==1 and fallback[0]['parameters']['options']['timeout']==270000
assert sum('retry gemini voiceover' in x['name'].lower() for x in w['nodes']) == 1
print('TTS_PROVIDER_BUDGET_REGRESSION_PASS')
