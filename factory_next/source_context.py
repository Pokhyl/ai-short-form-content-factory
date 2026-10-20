"""Bound generation context while full fetched originals remain citation authority."""
from collections import Counter,deque
from copy import deepcopy
import math
import re

MAX_SOURCE_CONTEXT_CHARS=18000

def _terms(text):
    return set(re.findall(r"[^\W_]{3,}",text.casefold(),re.UNICODE))

def _cited(value):
    result=set()
    if isinstance(value,dict):
        for key,item in value.items():
            if key=='span_id' and isinstance(item,str):result.add(item)
            elif key=='support_span_ids' and isinstance(item,list):
                result.update(v for v in item if isinstance(v,str))
            else:result.update(_cited(item))
    elif isinstance(value,list):
        for item in value:result.update(_cited(item))
    return result

def select_source_context(spans,topic,*,required=(),maximum=MAX_SOURCE_CONTEXT_CHARS):
    """Select exact whole spans; seed each source, then balanced lexical retrieval."""
    if sum(len(s['text']) for s in spans)<=maximum:return list(spans)
    by_id={s['id']:s for s in spans}
    if len(by_id)!=len(spans):raise ValueError('duplicate source span identity')
    chosen=set(required)&by_id.keys()
    used=sum(len(by_id[key]['text']) for key in chosen)
    if used>maximum:raise ValueError('cited source context exceeds generation budget')
    groups={}
    for span in spans:groups.setdefault(span['source_id'],[]).append(span)
    def add(span):
        nonlocal used
        if span['id'] in chosen:return True
        if used+len(span['text'])>maximum:return False
        chosen.add(span['id']);used+=len(span['text']);return True
    for group in groups.values():
        for span in group[:2]:add(span)
    query=_terms(topic)
    tokens=[_terms(s['text'])&query for s in spans]
    frequencies=Counter(term for row in tokens for term in row)
    score={s['id']:sum(1+math.log((len(spans)+1)/(frequencies[t]+1)) for t in row)
           for s,row in zip(spans,tokens)}
    queues=[deque(sorted(group,key=lambda s:(-score[s['id']],s['start'])))
            for group in groups.values()]
    while any(queues):
        for queue in queues:
            while queue:
                span=queue.popleft()
                if span['id'] not in chosen and add(span):break
    return [s for s in spans if s['id'] in chosen]

def _restrict_schema(schema,all_ids,included):
    if isinstance(schema,dict):
        result={key:_restrict_schema(value,all_ids,included) for key,value in schema.items()}
        values=schema.get('enum')
        if isinstance(values,list) and values and all(isinstance(v,str) for v in values) and set(values)<=all_ids:
            result['enum']=[value for value in values if value in included]
            if not result['enum']:raise ValueError('empty selected source span enum')
        return result
    if isinstance(schema,list):return [_restrict_schema(item,all_ids,included) for item in schema]
    return deepcopy(schema)

class SourceContextModel:
    """Only source-spans generation/repair requests are bounded; reviews stay exact."""
    def __init__(self,model,topic):
        self.model=model;self.topic=topic
    def generate(self,key,instruction,context,schema,**kwargs):
        spans=context.get('source_spans') if isinstance(context,dict) else None
        if not isinstance(spans,list) or sum(len(s['text']) for s in spans)<=MAX_SOURCE_CONTEXT_CHARS:
            return self.model.generate(key,instruction,context,schema,**kwargs)
        selected=select_source_context(spans,self.topic,required=_cited(context.get('rejected_draft',{})))
        included={s['id'] for s in selected}
        view=deepcopy(context);view['source_spans']=deepcopy(selected)
        view['source_context_policy']={'name':'exact-balanced-source-context-v1',
            'original_span_count':len(spans),'included_span_count':len(selected),
            'original_chars':sum(len(s['text']) for s in spans),
            'included_chars':sum(len(s['text']) for s in selected)}
        restricted=_restrict_schema(schema,{s['id'] for s in spans},included)
        return self.model.generate(key,instruction,view,restricted,**kwargs)
