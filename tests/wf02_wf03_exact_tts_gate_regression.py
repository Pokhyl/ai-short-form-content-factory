import json

def one(p):
 d=json.load(open(p,encoding='utf-8')); return d[0] if isinstance(d,list) else d
def node(w,n): return next(x for x in w['nodes'] if x.get('name')==n)
w2=one('n8n/workflows/WF02-plan-script-and-scenes.json')
w3=one('n8n/workflows/WF03-natural-edge-voice.json')
final=node(w2,'Build Final Grounded Script')['parameters']['jsCode']
assert 'prediction_is_advisory:true' in final and 'exact_tts_required:true' in final
q=node(w2,'Persist Grounded AI Narration')['parameters']['query']
assert 'prediction_is_advisory' in q and 'exact_tts_required' in q
eligible=node(w3,'Require Eligible Voiceover Job')['parameters']['jsCode']
assert 'exact_tts_required!==true' in eligible and 'prediction_is_advisory!==true' in eligible
measured=node(w3,'Evaluate Natural Voiceover')['parameters']['jsCode']
assert 'duration>=min' in measured and 'duration<=max' in measured
assert "Number(stored.rate_percent)!==0" in measured and "Number(stored.post_tempo_factor)!==1" in measured
print('WF02_WF03_EXACT_TTS_GATE_REGRESSION_PASS')
