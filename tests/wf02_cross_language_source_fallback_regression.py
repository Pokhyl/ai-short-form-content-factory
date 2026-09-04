import json
from pathlib import Path
w=json.loads(Path('n8n/workflows/WF02-plan-script-and-scenes.json').read_text())
w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
intent=n['Prepare Semantic Intent']['parameters']['jsCode']
writer=n['Prepare Grounded Script Prompt']['parameters']['jsCode']
assert 'regardless of the language in which it was typed' in intent
assert 'SELECTED OUTPUT LANGUAGE' in intent
assert 'search_query_en' in intent and 'search_query_target' in intent
assert 'script MUST be entirely in the selected output language' in writer
assert 'regardless of input-topic language or source language' in writer
assert 'Search Wikipedia Facts' not in n
print('WF02_CROSS_LANGUAGE_SOURCE_FALLBACK_REGRESSION_PASS')
