import json
w=json.load(open('n8n/workflows/WF04-visual-sourcing.json'));w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
code=n['Expand Reserved Story Assets']['parameters']['jsCode']
assert 'provider_asset_id' in code and 'provider:' in code
assert 'story.assets' in code
persist=n['Persist Reserved Visual']['parameters']['query']
assert 'ON CONFLICT(provider,provider_asset_id)' in persist
print('WF04_PROVIDER_SCOPED_IDENTITY_REGRESSION_PASS')
