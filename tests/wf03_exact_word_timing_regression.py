import json
w=json.load(open('n8n/workflows/WF03-natural-edge-voice.json'));w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
eval_code=n['Evaluate Natural Voiceover']['parameters']['jsCode']
timing=n['Build Exact Story Unit Timings']['parameters']['jsCode']
assert 'provider-word-timing-v1' in eval_code
assert 'word_timing' in eval_code
assert 'story.units' in timing
assert 'Provider timing diverges inside story unit' in timing
assert 'BEATS_BY_DURATION' not in timing
assert '15:6' not in timing and '30:10' not in timing and '45:14' not in timing and '60:18' not in timing
assert 'asset_id' in timing and 'claim_id' in timing and 'story_unit_id' in timing
print('WF03_EXACT_WORD_TIMING_REGRESSION_PASS')
