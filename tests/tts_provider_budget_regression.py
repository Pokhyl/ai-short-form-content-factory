import json,pathlib
s=pathlib.Path('services/media-worker/src/edge-provider-budget.mjs').read_text()
assert 'Math.max(25000, Math.min(40000' in s
w=json.load(open('n8n/workflows/WF03-natural-edge-voice.json'));w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
for removed in ['Generate Gemini Voiceover','Store Gemini Voiceover','Store Retried Gemini Voiceover','Attach Gemini Voice Metadata','Prepare Edge Fallback','Wait Once For TTS Quota','Retry Gemini Voiceover Once','Prepare Gemini TTS Retry']:
    assert removed not in n
fallback=n['Generate Edge Fallback']
assert fallback['parameters']['options']['timeout']==280000
assert 'target_duration_seconds' in fallback['parameters']['jsonBody']
assert w['connections']['Prepare Continuous Voiceover']['main'][0][0]['node']=='Generate Edge Fallback'
assert w['connections']['Resume Rewritten Voiceover']['main'][0][0]['node']=='Generate Edge Fallback'
assert w['connections']['Generate Edge Fallback']['main'][0][0]['node']=='Evaluate Natural Voiceover'
assert 'word_timing' in n['Evaluate Natural Voiceover']['parameters']['jsCode']
local=pathlib.Path('services/media-worker/src/piper-whisper-fallback.mjs').read_text()
assert 'Math.min(180000, 60000 + Math.round(target * 2000))' in local
worker=pathlib.Path('services/media-worker/src/server.mjs').read_text()
assert 'attempt <= 2' in worker
assert 'word_timing_path' in worker and 'word_timing: wordTiming' in worker
print('TTS_PROVIDER_BUDGET_REGRESSION_PASS')
