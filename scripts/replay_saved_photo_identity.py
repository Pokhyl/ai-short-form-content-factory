from pathlib import Path
import json,hashlib,subprocess
from material_first.photo_identity import fingerprint,same_photo
saved=json.loads(Path('/app/tests/material_first/fixtures/crab-distinct-observations.json').read_text())
expected={row['sha256']:row for row in saved['samples']}
found={}
for file in (Path('/data/catalog')/saved['origin_request']).glob('*/selected.*'):
 sha=hashlib.sha256(file.read_bytes()).hexdigest()
 if sha in expected:
  row=expected[sha]
  sample=fingerprint(file,sha,row['width'],row['height'])
  assert sample['rgb']==row['rgb'],'saved sample differs from actual original'
  found[row['id']]={'file':file,'sample':sample}
assert len(found)==2
first=found['wikimedia:516106'];other=found['wikimedia:139881470']
assert not same_photo(first['sample'],other['sample'])
variant=Path('/tmp/reencoded-copy.jpg')
subprocess.run(['ffmpeg','-v','error','-i',str(first['file']),'-vf','scale=960:960','-frames:v','1','-threads','1','-q:v','2',str(variant)],check=True,timeout=20)
sha=hashlib.sha256(variant.read_bytes()).hexdigest()
assert sha!=first['sample']['source_sha256']
assert same_photo(first['sample'],fingerprint(variant,sha,960,960))
print(json.dumps({'request':saved['origin_request'],'actual_original_samples':2,'saved_samples_match':True,'distinct_observations_retained':True,'actual_resized_jpeg_copy_rejected':True,'originals_read_only':True,'provider_calls':0,'tts_calls':0}))
