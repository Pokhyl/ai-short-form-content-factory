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
  self.text_vectors=texts
  return [float(score) for score in (images@texts.T)[0]]

 def check(self, image_path, subject, actions, caption='', competitors=None, competitor_subject='',extra_negatives=None,extra_positives=None):
  positive=[]
  templates={
   'heat':['Industrial heating and melting of {subject}.','A furnace melting {subject} material during manufacturing.'],
   'shape':['Industrial machinery forming and molding molten {subject}.','A worker shaping {subject} during its manufacturing process.'],
   'cool':['An annealing oven cooling {subject} after manufacturing.','Technical illustration of an annealing furnace for {subject}.'],
   'inspect':['A worker inspecting {subject} quality during manufacturing.','A photograph of a worker inspecting the quality of {subject}.','Quality control equipment inspecting {subject}.'],
   'production':['Factory production machinery manufacturing {subject}.','A person making {subject} by hand.']}
  for action in sorted(actions):
   for template in templates.get(action,[]):positive.append(template.format(subject=subject))
  if caption:positive.append('An image illustrating: '+caption)
  if not positive:positive=['A photograph of '+subject]
  positive.extend((extra_positives or [])[:4])
  negative=['A photograph of an unrelated landscape or animal.','A labeled line diagram, graph, chart or schematic.','A hand drawn illustration or painting.']
  negative.extend((extra_negatives or [])[:2])
  if actions:negative.append('Studio product photography of finished '+subject+' on a tabletop against a plain white background.')
  if 'shape' in actions:negative.append('A person attaching a cap or fitting to an already finished '+subject+'.')
  if 'glass' in subject.lower():negative.append('Metalworking, steel bars being heated and forged by a blacksmith.')
  base_count=len(negative);extra=(competitors or [])[:2];negative.extend(extra)
  descriptions=positive+negative
  if extra:descriptions.append('A photograph of a '+(competitor_subject or subject)+'.')
  scores=self.compare(image_path,descriptions);excluded=[];negative_indices=list(range(len(positive),len(positive)+base_count))
  for index,description in enumerate(extra):
   position=len(positive)+base_count+index
   # Near-identical text embeddings denote aliases, not competing classes.
   if float(self.text_vectors[position]@self.text_vectors[-1])>=.96:excluded.append(description)
   else:negative_indices.append(position)
  positive_score=max(scores[:len(positive)]);negative_score=max(scores[index] for index in negative_indices);margin=positive_score-negative_score
  return {'passed':positive_score>=0.24 and margin>=0.015,'positive_score':round(positive_score,6),'negative_score':round(negative_score,6),'margin':round(margin,6),'model_sha256':MODEL_SHA256,'descriptions':descriptions,'excluded_competitor_aliases':excluded,'scores':[round(x,6) for x in scores]}

 def check_person(self,image_path,identity,description=''):
  if not identity.get('entity_id') or not identity.get('basis'):raise ValueError('source-backed person identity required')
  content=['A photograph of a man.','A photograph of a woman.','A close up photograph of a human face.','A photograph of a man standing.','A photograph of a woman standing.','A photograph of a man sitting at a desk.','A photograph of a woman sitting at a desk.','A portrait photo of a man in a green shirt.','A portrait photo of a woman wearing a suit.','A portrait photo of a man wearing a suit and tie.','A photograph of two men shaking hands.','A photograph of men sitting together at a table.','A photograph of a man speaking into a microphone.','A photograph of a woman speaking into a microphone.','A photograph of two people standing together.']
  positive=content+['A portrait photograph of a person.','A photograph of people at an official meeting.','A photograph of politicians at an international summit.','A photograph of a public official speaking in front of flags.','A photograph of a person wearing a suit.']
  if description:positive.append('A photograph of '+description+'.')
  negative=['A photograph of an unrelated landscape or animal.','A drawing, poster or painting of a person.','An empty room or a flag with no people.','A photograph of a printed document, letter or certificate.','A photograph of a street billboard or propaganda poster.','A photograph of a billboard with a politician on it.','A statue or sculpture of a person.']
  descriptions=positive+negative;scores=self.compare(image_path,descriptions)
  positive_score=max(scores[:len(positive)]);negative_score=max(scores[len(positive):]);margin=positive_score-negative_score
  human_content_score=max(scores[:len(content)])
  return {'passed':positive_score>=.24 and human_content_score>=.24 and margin>=.015,'human_content_score':round(human_content_score,6),'positive_score':round(positive_score,6),'negative_score':round(negative_score,6),'margin':round(margin,6),'model_sha256':MODEL_SHA256,'descriptions':descriptions,'scores':[round(score,6) for score in scores],'identity_verification':identity,'pixel_check_scope':'photographic human content; subject identity comes from linked Commons metadata'}
