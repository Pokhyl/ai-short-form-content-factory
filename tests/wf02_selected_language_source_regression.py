import json
from pathlib import Path
w=json.loads(Path('n8n/workflows/WF02-plan-script-and-scenes.json').read_text())
w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
intent=n['Prepare Semantic Intent']['parameters']['jsCode']
writer=n['Prepare Grounded Script Prompt']['parameters']['jsCode']
final=n['Build Final Grounded Script']['parameters']['jsCode']
assert "const language=String(j.language_code" in intent
assert 'OUTPUT LANGUAGE: ${j.output_language_name} (${j.language_code})' in writer
assert "source_language:'en'" in final
assert "language_code:j.language_code" in final
assert 'selected output language' in writer.lower()
print('WF02_SELECTED_LANGUAGE_SOURCE_REGRESSION_PASS')
