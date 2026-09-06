import json
w=json.load(open('n8n/workflows/WF04-visual-sourcing.json'));w=w[0] if isinstance(w,list) else w
n={x['name']:x for x in w['nodes']}
code=n['Expand Reserved Story Assets']['parameters']['jsCode']
assert "canonical_subject:clean(j.fact_primary_title||j.topic)" in code
assert 'Fetch Canonical Media' not in n
assert 'Build Deterministic Visual Plans' not in n
print('WF04_CANONICAL_SUBJECT_EXECUTION_REGRESSION_PASS')
