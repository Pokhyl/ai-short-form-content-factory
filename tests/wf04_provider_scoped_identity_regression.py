import json
from pathlib import Path
w=json.loads(Path('n8n/workflows/WF04-visual-sourcing.json').read_text())
w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
code=n['Prepare Selected Download']['parameters']['jsCode']
assert "const identity=`${provider}:${assetId}`" in code
assert 'groups.get(identity)' in code
assert 'Asset ${identity} resolved to multiple download URLs' in code
assert 'groups.get(candidateId)' not in code
print('WF04_PROVIDER_SCOPED_IDENTITY_REGRESSION_PASS')
