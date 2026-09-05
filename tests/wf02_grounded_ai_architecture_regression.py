import json
w=json.load(open('n8n/workflows/WF02-plan-script-and-scenes.json',encoding='utf-8'))
if isinstance(w,list): w=w[0]
n={x['name']:x for x in w['nodes']}
required=['Prepare Semantic Intent','Resolve Topic Semantics','Discover Candidate Evidence','Build Evidence Comparison','Resolve Topic From Evidence','Validate Resolved Topic','Research Resolved Subject','Write Grounded Natural Script','Validate And Rewrite Script','Build Final Grounded Script','Persist Grounded AI Narration']
assert all(x in n for x in required)
names={x['name'] for x in w['nodes']}
assert 'Build Deterministic Narration' not in names
assert 'Search Wikipedia Facts' not in names
assert 'selected output language' in n['Prepare Semantic Intent']['parameters']['jsCode'].lower()
assert 'entirely in the selected output language' in n['Prepare Grounded Script Prompt']['parameters']['jsCode']
assert 'same chronological order as the future narration beats' in n['Prepare Grounded Script Prompt']['parameters']['jsCode']
assert '15:6,30:10,45:14,60:18' in n['Prepare Grounded Script Prompt']['parameters']['jsCode']
assert 'expectedVisualQueries' in n['Build Final Grounded Script']['parameters']['jsCode']
print('WF02_GROUNDED_AI_ARCHITECTURE_REGRESSION_PASS')
