"""Check apostrophe reconstruction and fail closed on unmatched speech."""
import uuid
from alignment_core import normalize_alignment_text,_lexical_tokens,_build_scene_timings

def check():
 assert normalize_alignment_text("в'язкою")==normalize_alignment_text('вязкою')
 text='Бджоли збирають нектар.'
 tokens=[{'text':' Бдж','offsets':{'from':0,'to':200}},{'text':'оли','offsets':{'from':200,'to':400}},{'text':' збирають','offsets':{'from':400,'to':1000}},{'text':' нектар.','offsets':{'from':1000,'to':1600}}]
 payload={'transcription':[{'text':text,'tokens':tokens}]}
 assert ''.join(t['normalized'] for t in _lexical_tokens(payload))==normalize_alignment_text(text)
 scenes=[{'scene_uuid':str(uuid.uuid4()),'scene_key':'0','narration':text}]
 result=_build_scene_timings(text,scenes,payload,1800)
 assert result['global_coverage']==1 and result['scene_timings'][0]['end_ms']==1600
 wrong='Бджоли живуть у вуликах.'
 try:_build_scene_timings(wrong,[{**scenes[0],'narration':wrong}],payload,1800);raise AssertionError('unmatched speech accepted')
 except ValueError as error:assert 'coverage below' in str(error)
 for number,word in [(5,"п'ять"),(15,"п'ятнадцять"),(50,"п'ятдесят"),(9,"дев'ять")]:
  assert normalize_alignment_text(word)==str(number)
 # Actual failure: the apostrophe occupied a separate timestamped Whisper token.
 split={'transcription':[{'text':"П'ять років.",'tokens':[{'text':' П','offsets':{'from':0,'to':100}},{'text':"'",'offsets':{'from':100,'to':110}},{'text':'ять','offsets':{'from':110,'to':300}},{'text':' років.','offsets':{'from':300,'to':700}}]}]}
 assert ''.join(token['normalized'] for token in _lexical_tokens(split))=='5років'
 five=[{'scene_uuid':str(uuid.uuid4()),'scene_key':'0','narration':'5 років.'}]
 recovered=_build_scene_timings('5 років.',five,split,800)
 assert recovered['global_coverage']==1 and recovered['scene_timings'][0]['end_ms']==700
 print('PASS alignment: lexical subwords reconstruct text, apostrophes normalize, actual timing retained, unmatched speech rejected')
if __name__=='__main__':check()
