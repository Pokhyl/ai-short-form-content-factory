"""Offline CLIP image/text comparison using checksum-pinned quantized ONNX weights."""
import hashlib
import json
import os
from pathlib import Path
import threading
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageOps
from tokenizers import Tokenizer

MODEL_SHA256='0898a3facfdb27f0a041e57649b4989cfd094e4a0040d6ae75ed69917dfc7328'

class VisualVerifier:
 def __init__(self, directory=None):
  self.directory=Path(directory or os.getenv('VISUAL_MODEL_DIR','/models/clip'))
  path=self.directory/'model_quantized.onnx'
  digest=hashlib.sha256()
  with path.open('rb') as stream:
   for chunk in iter(lambda:stream.read(1048576),b''):digest.update(chunk)
  if digest.hexdigest()!=MODEL_SHA256:raise ValueError('visual model integrity check failed')
  self.config=json.loads((self.directory/'preprocessor_config.json').read_text())
  self.tokenizer=Tokenizer.from_file(str(self.directory/'tokenizer.json'))
  self.tokenizer.enable_truncation(max_length=77)
  self.tokenizer.enable_padding(length=77,pad_id=49407,pad_token='<|endoftext|>')
  options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
  options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
  self.session=ort.InferenceSession(str(path),sess_options=options,providers=['CPUExecutionProvider'])
  self.lock=threading.Lock()
 def compare(self, image_path, descriptions):
  if not descriptions or len(descriptions)>32:raise ValueError('visual comparison requires 1-32 descriptions')
  crop=self.config.get('crop_size',{'height':224,'width':224})
  size=self.config.get('size',{'shortest_edge':224});short=size.get('shortest_edge',224) if isinstance(size,dict) else size
  with Image.open(image_path) as source:
   image=ImageOps.exif_transpose(source).convert('RGB')
   ratio=short/min(image.size)
   image=image.resize((int(image.width*ratio),int(image.height*ratio)),Image.Resampling.BICUBIC)
   left=(image.width-crop['width'])//2;top=(image.height-crop['height'])//2
   image=image.crop((left,top,left+crop['width'],top+crop['height']))
   pixels=np.asarray(image,dtype=np.float32)/255.0
  mean=np.asarray(self.config['image_mean'],dtype=np.float32)
  std=np.asarray(self.config['image_std'],dtype=np.float32)
  pixels=np.transpose((pixels-mean)/std,(2,0,1))[None,...].astype(np.float32)
  with self.lock:
   encoded=self.tokenizer.encode_batch(descriptions)
   values={'input_ids':np.asarray([x.ids for x in encoded],dtype=np.int64),'attention_mask':np.asarray([x.attention_mask for x in encoded],dtype=np.int64),'pixel_values':pixels}
   feed={input.name:values[input.name] for input in self.session.get_inputs()}
   results=dict(zip([output.name for output in self.session.get_outputs()],self.session.run(None,feed)))
  if 'image_embeds' not in results or 'text_embeds' not in results:raise ValueError('visual model lacks required embedding outputs')
  images=results['image_embeds'];texts=results['text_embeds']
  images=images/np.maximum(np.linalg.norm(images,axis=-1,keepdims=True),1e-12)
  texts=texts/np.maximum(np.linalg.norm(texts,axis=-1,keepdims=True),1e-12)
  return [float(score) for score in (images@texts.T)[0]]

 def check(self, image_path, subject, actions, caption=''):
  positive=[]
  templates={
   'heat':['Industrial heating and melting of {subject}.','A furnace melting {subject} material during manufacturing.'],
   'shape':['Industrial machinery forming and molding molten {subject}.','A worker shaping {subject} during its manufacturing process.'],
   'cool':['An annealing oven cooling {subject} after manufacturing.','Technical illustration of an annealing furnace for {subject}.'],
   'inspect':['A worker inspecting {subject} quality during manufacturing.','A photograph of a worker inspecting the quality of {subject}.','Quality control equipment inspecting {subject}.'],
   'production':['Factory production machinery manufacturing {subject}.']}
  for action in sorted(actions):
   for template in templates.get(action,[]):positive.append(template.format(subject=subject))
  if caption:positive.append('An image illustrating: '+caption)
  if not positive:positive=['A photograph of '+subject]
  negative=['A photograph of an unrelated landscape or animal.']
  if actions:negative.append('Studio product photography of finished '+subject+' on a tabletop against a plain white background.')
  if 'shape' in actions:negative.append('A person attaching a cap or fitting to an already finished '+subject+'.')
  if 'glass' in subject.lower():negative.append('Metalworking, steel bars being heated and forged by a blacksmith.')
  scores=self.compare(image_path,positive+negative)
  positive_score=max(scores[:len(positive)]);negative_score=max(scores[len(positive):]);margin=positive_score-negative_score
  return {'passed':positive_score>=0.24 and margin>=0.015,'positive_score':round(positive_score,6),'negative_score':round(negative_score,6),'margin':round(margin,6),'model_sha256':MODEL_SHA256,'descriptions':positive+negative,'scores':[round(x,6) for x in scores]}
