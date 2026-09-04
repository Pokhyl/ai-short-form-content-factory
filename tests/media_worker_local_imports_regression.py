from pathlib import Path
import re
src=Path('services/media-worker/src/server.mjs').read_text()
mods=re.findall(r'from\s+"(\./[^"]+)"',src)
missing=[]
for mod in mods:
    rel=mod[2:]
    path=Path('services/media-worker/src')/rel
    if not path.exists(): missing.append(str(path))
assert not missing, f'missing local media-worker modules: {missing}'
print('MEDIA_WORKER_LOCAL_IMPORTS_REGRESSION_PASS')
