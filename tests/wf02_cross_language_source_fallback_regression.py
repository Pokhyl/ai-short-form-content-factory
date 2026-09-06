import json
from pathlib import Path
w=json.loads(Path('n8n/workflows/WF02-plan-script-and-scenes.json').read_text()); w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
intent=n['Prepare Semantic Intent']['parameters']['jsCode']
story=n['Prepare Inventory Grounded Story']['parameters']['jsCode']
assert 'language of the topic is independent from the selected output language' in intent
assert 'SELECTED OUTPUT LANGUAGE' in intent
assert 'discovery_query' in intent and 'Do not choose a winner yet' in intent
assert 'OUTPUT LANGUAGE: ${x.output_language_name} (${x.language_code})' in story
assert 'Research Resolved Subject' in n
assert 'Search Wikipedia Facts' not in n
assert 'Prepare Grounded Script Prompt' not in n
print('WF02_CROSS_LANGUAGE_SOURCE_FALLBACK_REGRESSION_PASS')
