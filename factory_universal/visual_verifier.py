"""Offline CLIP image/text comparison using checksum-pinned quantized ONNX weights."""
import hashlib
import json
import os
from pathlib import Path
import threading
from collections import OrderedDict
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
  self.image_vectors=OrderedDict();self.description_vectors=OrderedDict()
 def compare(self, image_path, descriptions, use_cache=True):
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
  image_key=hashlib.sha256(Path(image_path).read_bytes()).hexdigest();text_key=tuple(descriptions)
  with self.lock:
   images=self.image_vectors.get(image_key) if use_cache else None;texts=self.description_vectors.get(text_key) if use_cache else None
   if images is None or texts is None:
    # CLIP has independent encoders. Keep each full text batch unchanged;
    # when its vectors are cached, one dummy text suffices to encode a new image.
    encoded=self.tokenizer.encode_batch(descriptions if texts is None else descriptions[:1])
    values={'input_ids':np.asarray([x.ids for x in encoded],dtype=np.int64),'attention_mask':np.asarray([x.attention_mask for x in encoded],dtype=np.int64),'pixel_values':pixels}
    feed={input.name:values[input.name] for input in self.session.get_inputs()}
    results=dict(zip([output.name for output in self.session.get_outputs()],self.session.run(None,feed)))
    if 'image_embeds' not in results or 'text_embeds' not in results:raise ValueError('visual model lacks required embedding outputs')
    if images is None:
     images=results['image_embeds'];images=images/np.maximum(np.linalg.norm(images,axis=-1,keepdims=True),1e-12)
     if use_cache:self.image_vectors[image_key]=images
    if texts is None:
     texts=results['text_embeds'];texts=texts/np.maximum(np.linalg.norm(texts,axis=-1,keepdims=True),1e-12)
     if use_cache:self.description_vectors[text_key]=texts
   if use_cache:self.image_vectors.move_to_end(image_key);self.description_vectors.move_to_end(text_key)
   while len(self.image_vectors)>256:self.image_vectors.popitem(last=False)
   while len(self.description_vectors)>128:self.description_vectors.popitem(last=False)
   self.text_vectors=texts
   return [float(score) for score in (images@texts.T)[0]]

 def compare_batches(self,image_path,descriptions,use_cache=True):
  # Preserve every positive and negative description within the encoder's batch bound.
  if not descriptions:raise ValueError('visual comparison requires descriptions')
  return [score for start in range(0,len(descriptions),32) for score in self.compare(image_path,descriptions[start:start+32],use_cache=use_cache)]

 def check(self, image_path, subject, actions, caption='', competitors=None, competitor_subject='',extra_negatives=None,extra_positives=None):
  positive=[]
  templates={
   'heat':['Industrial equipment heating {subject}.','A worker heating {subject} during manufacturing.'],
   'melt':['A furnace melting {subject} material.','Molten {subject} in a manufacturing furnace.'],
   'drain':['Wet {subject} pulp draining through a mesh screen.','A forming screen removing water from {subject} fibers.','A photograph of a wire screen or mould used in {subject} production.'],
   'press':['Press rollers squeezing water out of wet {subject}.','A hydraulic press compressing {subject} during manufacturing.','A photograph of a press machine used in {subject} production.'],
   'dry':['Sheets of {subject} drying on racks.','Industrial dryers drying {subject} sheets.'],
   'cut':['Industrial equipment cutting {subject}.','Slitting blades trimming {subject} sheets.'],
   'mix':['A vat mixing {subject} raw material.','Industrial mixers blending {subject}.'],
   'shape':['Industrial machinery forming and molding {subject}.','A worker shaping {subject} during its manufacturing process.'],
   'cool':['An annealing oven cooling {subject} after manufacturing.','Technical illustration of an annealing furnace for {subject}.'],
   'inspect':['A worker inspecting {subject} quality during manufacturing.','A photograph of a worker inspecting the quality of {subject}.','Quality control equipment inspecting {subject}.'],
   'production':['A photograph of industrial {subject} production machinery.','An archival photograph of {subject} manufacturing inside a factory.','A photograph of {subject} being made by hand.']}
  for action in sorted(actions):
   for template in templates.get(action,[]):positive.append(template.format(subject=subject))
  if caption:positive.append('An image illustrating: '+caption)
  if not positive:positive=['A photograph of '+subject]
  positive.extend((extra_positives or [])[:4])
  negative=['A photograph of an unrelated landscape or animal.','A labeled line diagram, graph, chart or schematic.','A hand drawn illustration or painting.','A black and white woodcut engraving or historical line drawing.','A geographic map or a city locator map.','A photograph of a printed document, letter, certificate or text page.']
  negative.extend((extra_negatives or [])[:min(8,max(0,24-len(positive)-len(negative)))])
  if actions and actions!={'dry'}:negative.append('A product photograph of finished '+subject+' without people or machinery.')
  if actions and actions!={'production'}:negative.append('An exterior view of a factory building with no visible manufacturing operation.')
  if 'press' in actions:negative.append('A cutting blade slitting already finished sheets.')
  if 'dry' in actions:negative.append('A steaming vat cooking or boiling wet pulp.')
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

 def check_photograph(self,image_path):
  positive=['A close-up photograph of a metal medal or coin.','A photograph of a laboratory sample in a vial.','A photograph of a car.','A photograph of a rocket or spacecraft.','A photograph of a ship.','A photograph of a building.','A photograph of industrial machinery.','A photograph of a physical object.','A photograph of a landscape.','A photograph of people.','A black and white historical photograph.','A scientific microscope photograph.','A photograph of an animal.','An astronomical photograph taken by a telescope.','A photograph of laboratory equipment.','A photograph of green leaves and growing plants.','A close-up photograph of a metal plate with engraved letters.','A close-up photograph of a wire mesh screen.','A photograph of manufacturing tools on display in a museum.','A photograph of paper sheets drying on racks.']
  # Cover civic and performance photographs without naming the requested subject.
  # Identity and scene relevance remain independent gates; the genre margin stays .015.
  positive+=['A photograph of people casting votes at a polling station.','A photograph of people at a public ceremony.','A photograph of a politician speaking at a lectern.','A photograph of actors performing on a stage.','A photograph of a crowd at a public event.','A photograph of two people shaking hands.','A photograph of a person signing a document.']
  negative=['A digital advertisement, a marketing banner or a promotional graphic.','A screenshot of a computer program or website.','A standalone logo or wordmark on a plain background.','A vector drawing, a diagram, a graph or an illustration.','An anatomical illustration with arrows and text labels.','A scientific schematic of parts and connections.','A scientific chart on a white background with lines and numeric axes.','A colorful educational diagram with arrows and labels.','A scientific flowchart or infographic explaining a process.','A document, certificate or handwriting.','A scanned book or calendar page containing a printed photograph and surrounding text.','A painting, woodcut, engraving or AI-generated illustration.']
  scores=self.compare_batches(image_path,positive+negative)
  best=max(scores[:len(positive)]);wrong=max(scores[len(positive):]);margin=best-wrong
  return {'passed':margin>=.015,'policy':'contrastive photographic genre; independent subject gate requires 0.24 and 0.015','positive_score':round(best,6),'negative_score':round(wrong,6),'margin':round(margin,6),'model_sha256':MODEL_SHA256,'descriptions':positive+negative,'scores':[round(score,6) for score in scores]}

 def check_person(self,image_path,identity,description=''):
  if not identity.get('entity_id') or not identity.get('basis'):raise ValueError('source-backed person identity required')
  content=['A photograph of a man.','A photograph of a woman.','A close up photograph of a human face.','A photograph of a man standing.','A photograph of a woman standing.','A photograph of a man sitting at a desk.','A photograph of a woman sitting at a desk.','A portrait photo of a man in a green shirt.','A portrait photo of a woman wearing a suit.','A portrait photo of a man wearing a suit and tie.','A photograph of two men shaking hands.','A photograph of men sitting together at a table.','A photograph of a man speaking into a microphone.','A photograph of a woman speaking into a microphone.','A photograph of two people standing together.']
  content+=['A photograph of a man casting a ballot into a ballot box.','A photograph of people voting at a polling station.','A photograph of a man taking an oath of office.','A photograph of actors performing on a stage.']
  positive=content+['A portrait photograph of a person.','A photograph of people at an official meeting.','A photograph of politicians at an international summit.','A photograph of a public official speaking in front of flags.','A photograph of a person wearing a suit.']
  if description:positive.append('A photograph of '+description+'.')
  negative=['A photograph of an unrelated landscape or animal.','A drawing, poster or painting of a person.','An empty room or a flag with no people.','A photograph of a printed document, letter or certificate.','A photograph of a street billboard or propaganda poster.','A photograph of a billboard with a politician on it.','A screenshot of a website, app interface or social media post.','A statue or sculpture of a person.']
  descriptions=positive+negative;scores=self.compare(image_path,descriptions)
  positive_score=max(scores[:len(positive)]);negative_score=max(scores[len(positive):]);margin=positive_score-negative_score
  human_content_score=max(scores[:len(content)])
  return {'passed':positive_score>=.24 and human_content_score>=.24 and margin>=.015,'human_content_score':round(human_content_score,6),'positive_score':round(positive_score,6),'negative_score':round(negative_score,6),'margin':round(margin,6),'model_sha256':MODEL_SHA256,'descriptions':descriptions,'scores':[round(score,6) for score in scores],'identity_verification':identity,'pixel_check_scope':'photographic human content; subject identity comes from linked Commons metadata'}
