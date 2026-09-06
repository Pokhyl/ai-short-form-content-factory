import json
from pathlib import Path
schema=Path('db/init/001_init.sql').read_text()
migration=Path('db/migrations/022_inventory_first_story_package.sql').read_text()
wf=Path('n8n/workflows/WF02-plan-script-and-scenes.json').read_text()
assert 'story_package jsonb' in schema
assert "inventory-first-story-v1" in schema and "inventory-first-story-v1" in migration
assert "jsonb_array_length(story_package->'assets') = jsonb_array_length(story_package->'units')" in migration
assert 'visual_search_queries_en=NULL' in wf
assert 'story_package' in wf
assert 'BETWEEN 2 AND 12' in wf
print('INVENTORY_FIRST_STORY_SCHEMA_REGRESSION_PASS')
