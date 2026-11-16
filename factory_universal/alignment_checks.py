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
 print('PASS alignment: lexical subwords reconstruct text, apostrophes normalize, actual timing retained, unmatched speech rejected')
if __name__=='__main__':check()
