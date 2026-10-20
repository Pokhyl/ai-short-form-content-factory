from pathlib import Path
import os,json,time
from types import SimpleNamespace
from factory_v3.runtime import Runtime,load_settings
from factory_next.wiring import narrative_model_for
from factory_next.preparation import PreparationStages
base=Path('/evidence')
plan=json.loads((base/'no-retry-dna-research-boundary-plan-20261020.json').read_text())
fd=os.open(base/'no-retry-dna-research-boundary-started-20261020.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
os.close(fd)
started=time.monotonic()
result={'id':plan['id'],'source_revision':plan['source_revision']}
class Limited:
    def __init__(self,base):self.base=base;self.count=0
    def run(self,key,kind,request,invoke,**kwargs):
        if kind=='gemini':
            if self.count>=4:raise ValueError('bounded diagnostic call ceiling')
            self.count+=1
        return self.base.run(key,kind,request,invoke,**kwargs)
try:
    runtime=Runtime(load_settings('/run/factory-v3/settings.json'),'/data',plan['source_revision'])
    original=json.loads((Path('/data/factory-next-states')/plan['source_job']/'state.json').read_text())
    sources=original['outputs']['research']['evidence']['sources']
    request=original['request']
    runtime.create(plan['id'],request['topic'],request['language'],request['seconds'],
                   visual_validation_mode='gemini',_factory_next=True)
    producer=runtime.producer(plan['id'])
    model=narrative_model_for(runtime,producer)
    assert model.model=='gemini-3.8-flash'
    limited=Limited(model.calls);model.calls=limited
    producer.operations.source=SimpleNamespace(fetch=lambda topic,language:sources)
    stages=PreparationStages('/data',producer.operations,producer.authorize,narrative_model=model)
    brief=stages.research({'request':request})
    result.update(status='reviewed',calls=limited.count,research=brief)
except BaseException as error:
    result.update(status='failed',error_type=type(error).__name__)
    if hasattr(error,'receipt'):result['failure_receipt']=error.receipt
finally:
    result['elapsed_seconds']=round(time.monotonic()-started,3)
    (base/'no-retry-dna-research-boundary-result-20261020.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='research'}))
