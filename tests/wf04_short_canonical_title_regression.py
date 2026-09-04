import json
from pathlib import Path
w=json.loads(Path('n8n/workflows/WF04-visual-sourcing.json').read_text())
code=next(n for n in w[0]['nodes'] if n['name']=='Build Deterministic Visual Plans')['parameters']['jsCode']
assert 't.length>=3' in code
assert 't.length>=4&&!COMMON' not in code
print('WF04_SHORT_CANONICAL_TITLE_REGRESSION_PASS')
