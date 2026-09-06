import json
w=json.load(open('n8n/workflows/WF02-plan-script-and-scenes.json',encoding='utf-8')); w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
required=['Prepare Semantic Intent','Resolve Topic Semantics','Discover Candidate Evidence','Build Evidence Comparison','Resolve Topic From Evidence','Validate Resolved Topic','Research Resolved Subject','Prepare Candidate Claims','Draft Candidate Claims','Validate Candidate Claims','Discover Pre-Script Visual Inventory','Prepare Inventory Review Batches','Review Inventory Candidate Images','Select Verified Claim Inventory','Prepare Inventory Grounded Story','Write Inventory Grounded Story','Build Final Inventory Story','Persist Inventory First Story']
assert all(x in n for x in required)
names=set(n)
for old in ['Build Deterministic Narration','Search Wikipedia Facts','Prepare Grounded Script Prompt','Write Grounded Natural Script','Validate And Rewrite Script','Build Final Grounded Script']:
    assert old not in names
claim=n['Prepare Candidate Claims']['parameters']['jsCode']
story=n['Prepare Inventory Grounded Story']['parameters']['jsCode']
final=n['Build Final Inventory Story']['parameters']['jsCode']
assert 'Do NOT write the final narration yet' in claim
assert 'verified real image reserved before narration' in story
assert "version:'inventory-first-story-v1'" in final
assert 'visual_search_queries_en' not in final
print('WF02_GROUNDED_AI_ARCHITECTURE_REGRESSION_PASS')
