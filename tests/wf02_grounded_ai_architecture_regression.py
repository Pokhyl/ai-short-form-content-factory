import json
w=json.load(open('n8n/workflows/WF02-plan-script-and-scenes.json',encoding='utf-8'));w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
required=['Prepare Semantic Intent','Resolve Topic Semantics','Discover Candidate Evidence','Build Evidence Comparison','Resolve Topic From Evidence','Validate Resolved Topic','Research Resolved Subject','Prepare Visual Exploration','Draft Visual Exploration','Validate Visual Exploration','Discover Pre-Claim Visual Inventory','Prepare Pre-Claim Review Batches','Review Pre-Claim Visual Inventory','Select Pre-Claim Visual Inventory','Prepare Candidate Claims','Draft Candidate Claims','Validate Candidate Claims','Prepare Inventory Grounded Story','Write Inventory Grounded Story','Build Final Inventory Story','Persist Inventory First Story']
assert all(x in n for x in required)
for old in ['Discover Pre-Script Visual Inventory','Prepare Inventory Review Batches','Review Inventory Candidate Images','Select Verified Claim Inventory','Loop Inventory Review Batches']:
 assert old not in n
claim=n['Prepare Candidate Claims']['parameters']['jsCode'];story=n['Prepare Inventory Grounded Story']['parameters']['jsCode'];final=n['Build Final Inventory Story']['parameters']['jsCode']
assert 'PIXEL-DERIVED VISUAL FACTS' in claim and 'photo is never mandatory' in claim
assert 'No new media search exists after this point' in story
assert "version:'visual-facts-story-v1'" in final and "editorial_contract_version:'storyboard-v1'" in final
assert 'visual_search_queries_en' not in final
print('WF02_GROUNDED_AI_ARCHITECTURE_REGRESSION_PASS')
