"""Compare cached CLIP scores with full encoder execution on local real images."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
from visual_verifier import VisualVerifier, MODEL_SHA256

parser=argparse.ArgumentParser()
parser.add_argument('--images',nargs='+',required=True)
parser.add_argument('--receipt',required=True)
args=parser.parse_args()
images=[Path(path) for path in args.images]
verifier=VisualVerifier()
descriptions=verifier.check_photograph(images[0])['descriptions']
verifier.image_vectors.clear();verifier.description_vectors.clear()
rows=[]
for path in images:
 start=time.monotonic();reference=verifier.compare_batches(path,descriptions,use_cache=False);baseline=time.monotonic()-start
 start=time.monotonic();observed=verifier.compare_batches(path,descriptions);cached=time.monotonic()-start
 error=float(np.max(np.abs(np.asarray(reference)-np.asarray(observed))))
 assert error<1e-6,(str(path),error)
 # A second, distinct text context reuses the image encoder but retains its full text batch.
 other=['A photograph of physical manufacturing tools.','A scientific diagram.','A photograph of growing plants.']
 human=verifier.check_person(path,{'entity_id':'diagnostic','basis':'content-only encoder equivalence check'})['descriptions']
 for context in (other,human):
  expected=verifier.compare(path,context,use_cache=False)
  actual=verifier.compare(path,context)
  assert np.allclose(expected,actual,rtol=0,atol=1e-6),str(path)
 start=time.monotonic();again=verifier.compare_batches(path,descriptions);warm=time.monotonic()-start
 assert np.allclose(reference,again,rtol=0,atol=1e-6)
 rows.append({'image':str(path),'maximum_score_error':error,'full_encoder_seconds':baseline,'cached_seconds':cached,'warm_seconds':warm})
result={'model_sha256':MODEL_SHA256,'images':len(images),'scores_equivalent':True,'image_cache_limit':256,'text_batch_cache_limit':128,'results':rows}
Path(args.receipt).write_text(json.dumps(result,indent=2))
print(json.dumps(result))
