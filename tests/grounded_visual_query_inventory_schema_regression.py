from pathlib import Path

migration = Path('db/migrations/021_expand_grounded_visual_query_inventory.sql').read_text()
workflow = Path('n8n/workflows/WF02-plan-script-and-scenes.json').read_text()
discovery = Path('services/media-worker/src/visual-discovery.mjs').read_text()

assert 'BETWEEN 6 AND 18' in migration
assert 'BETWEEN 6 AND 18' in workflow
assert '15:6,30:10,45:14,60:18' in workflow
assert 'slice(0, 18)' in discovery
print('GROUNDED_VISUAL_QUERY_INVENTORY_SCHEMA_REGRESSION_PASS')
