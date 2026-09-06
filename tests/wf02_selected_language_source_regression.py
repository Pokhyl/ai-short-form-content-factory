import json
from pathlib import Path
w=json.loads(Path('n8n/workflows/WF02-plan-script-and-scenes.json').read_text()); w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
intent=n['Prepare Semantic Intent']['parameters']['jsCode']
story=n['Prepare Inventory Grounded Story']['parameters']['jsCode']
final=n['Build Final Inventory Story']['parameters']['jsCode']
assert "const language=String(j.language_code" in intent
assert 'OUTPUT LANGUAGE: ${x.output_language_name} (${x.language_code})' in story
assert "source_language:'en'" in final
assert "language_code:base.language_code" in final
assert 'selected output language' in story.lower()
print('WF02_SELECTED_LANGUAGE_SOURCE_REGRESSION_PASS')
