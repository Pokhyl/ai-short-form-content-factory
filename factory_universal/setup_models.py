#!/usr/bin/env python3
"""Install the pinned local image verification model; no API key is needed."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
from source_translation import MODEL, MODEL_HASHES, QUERY_MODEL, QUERY_HASHES

REVISION='6b7c523703ae26e39be4b03774966f8571c7f523'
FILES=[
 ('onnx/model_quantized.onnx','model_quantized.onnx',153695702,'0898a3facfdb27f0a041e57649b4989cfd094e4a0040d6ae75ed69917dfc7328'),
 ('tokenizer.json','tokenizer.json',2224119,'f7f3b7af117d467b58374797691a6438d3e6b9e9cef800dfd5dced7f697a90cd'),
 ('preprocessor_config.json','preprocessor_config.json',520,'6f638fb9401a6d6296feff533ee7efe657b787c49f954f82f5906b36ef2a1b1f')]
def digest(path):
 value=hashlib.sha256()
 with path.open('rb') as stream:
  for chunk in iter(lambda:stream.read(1048576),b''):value.update(chunk)
 return value.hexdigest()
def install(directory,repository,revision,files):
 directory.mkdir(parents=True,exist_ok=True)
 for remote,name,size,expected in files:
  target=directory/name
  if target.is_file() and target.stat().st_size==size and digest(target)==expected:continue
  if shutil.disk_usage(directory).free<2_000_000_000:raise RuntimeError('need at least 2 GB free before installing model files')
  partial=directory/(name+'.partial');used=0
  try:
   url='https://huggingface.co/'+repository+'/resolve/'+revision+'/'+remote
   with urllib.request.urlopen(url,timeout=60) as response,partial.open('wb') as stream:
    while True:
     chunk=response.read(1048576)
     if not chunk:break
     used+=len(chunk)
     if used>size:raise RuntimeError('download exceeds pinned file size: '+name)
     stream.write(chunk)
   if used!=size or digest(partial)!=expected:raise RuntimeError('model integrity check failed: '+name)
   partial.replace(target)
  finally:partial.unlink(missing_ok=True)
 (directory/'revision.json').write_text(json.dumps({'repository':repository,'revision':revision,'files':[{'name':name,'bytes':size,'sha256':sha} for _,name,size,sha in files]},indent=2))
 print(repository+' ready; all file sizes and checksums verified.')

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--directory',type=Path)
 parser.add_argument('--translation',action='store_true')
 args=parser.parse_args()
 if not args.translation:
  install(args.directory or Path('/var/lib/factory-rebuild/models/clip'),'Xenova/clip-vit-base-patch32',REVISION,FILES)
  return
 directory=args.directory or Path('/var/lib/factory-universal/models/translation')
 for folder,repository,model,hashes,sizes in (
  ('from-english','NothingSoftware/opus-mt-tc-big-en-zle-ct2-int8',MODEL,MODEL_HASHES,
   (233,242630403,2152164,802747,1017004)),
  ('to-english','mults/hplt-translate-uk-en-ct2-int8',QUERY_MODEL,QUERY_HASHES,
   (231,2450722,1642012,82193357)),
 ):
  files=[(name,name,size,checksum) for (name,checksum),size in zip(hashes.items(),sizes,strict=True)]
  install(directory/folder,repository,model.split('@',1)[1],files)
if __name__=='__main__':main()
