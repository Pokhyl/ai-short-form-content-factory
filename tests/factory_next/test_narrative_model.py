import unittest
from types import SimpleNamespace
from copy import deepcopy
from factory_next.wiring import narrative_model_for

class NarrativeModelProofTests(unittest.TestCase):
    def setUp(self):
        self.proof={'model':'gemini-3.8-flash','billing_enabled':False,
            'standard_free_tier':True,'verification_id':'actual-evaluation',
            'project_id':'project-one','credential_sha256':'digest-one'}
        self.runtime=SimpleNamespace(settings={'free_tier_proof':{
            'project_id':'project-one','credential_sha256':'digest-one'},
            'factory_next_narrative_proof':self.proof})
        self.calls=object()
        self.original=SimpleNamespace(model='gemini-3.1-flash-lite',calls=self.calls)
        self.producer=SimpleNamespace(operations=SimpleNamespace(gemini=self.original))
    def test_primary_free_model_can_be_selected_for_narrative_with_shared_budget(self):
        self.proof['model']='gemini-3.1-flash-lite'
        selected=narrative_model_for(self.runtime,self.producer)
        self.assertEqual(selected.model,'gemini-3.1-flash-lite')
        self.assertIs(selected.calls,self.calls)
        self.assertTrue(selected.require_fact_coverage)
        self.assertTrue(selected.fact_owned_story)
        self.assertEqual(self.original.model,'gemini-3.1-flash-lite')
        self.assertFalse(hasattr(selected,'default_thinking_level'))

    def test_verified_fixed_model_keeps_durable_meter_and_original_model(self):
        selected=narrative_model_for(self.runtime,self.producer)
        self.assertEqual(selected.model,'gemini-3.8-flash')
        self.assertIs(selected.calls,self.calls)
        self.assertEqual(self.original.model,'gemini-3.1-flash-lite')
    def test_verified_lite_selection_keeps_shared_budget_and_is_not_fallback(self):
        self.proof['model']='gemini-3.5-flash-lite'
        selected=narrative_model_for(self.runtime,self.producer)
        self.assertEqual(selected.model,'gemini-3.5-flash-lite')
        self.assertEqual(selected.default_thinking_level,'high')
        self.assertFalse(hasattr(self.original,'default_thinking_level'))
        self.assertIs(selected.calls,self.calls)
        self.assertEqual(self.original.model,'gemini-3.1-flash-lite')
        self.proof['billing_enabled']=True
        with self.assertRaises(ValueError):narrative_model_for(self.runtime,self.producer)
    def test_missing_opt_in_preserves_existing_behavior(self):
        del self.runtime.settings['factory_next_narrative_proof']
        self.assertIsNone(narrative_model_for(self.runtime,self.producer))
    def test_paid_unknown_model_and_wrong_credentials_are_rejected(self):
        for key,value in [('model','gemini-paid'),('billing_enabled',True),
                ('standard_free_tier',False),('project_id','other-project'),
                ('credential_sha256','other-key'),('verification_id','')]:
            with self.subTest(key=key):
                runtime=deepcopy(self.runtime)
                runtime.settings['factory_next_narrative_proof'][key]=value
                with self.assertRaisesRegex(ValueError,'free-tier'):
                    narrative_model_for(runtime,self.producer)
    def test_partial_proof_cannot_enable_model(self):
        self.runtime.settings['factory_next_narrative_proof']={}
        with self.assertRaises(ValueError):narrative_model_for(self.runtime,self.producer)

class ResearchModelRoutingTests(unittest.TestCase):
    def test_research_generation_and_review_share_verified_model_meter(self):
        import hashlib
        from factory_next.preparation import PreparationStages
        from factory_v3.gemini import obj,string
        text='Three independently supported source claims.'
        evidence={'sources':[{'id':'s1','url':'https://example.org/source','title':'Source',
                   'text':text,'sha256':hashlib.sha256(text.encode()).hexdigest()}],
                  'facts':[{'id':'f'+str(i),'text':'Source claim '+str(i),
                    'support':[{'source_id':'s1','quote':text}]} for i in range(1,4)]}
        class Model:
            def __init__(self):self.calls=[]
            def generate(self,key,*args,**kwargs):self.calls.append(key)
        class Operations:
            def research(self,request):
                self.gemini.generate('generation','',{},obj({'result':string()}))
                self.gemini.generate('independent-review','',{},obj({'result':string()}))
                return {'evidence':evidence,'required_fact_ids':['f1','f2','f3'],'queries':[]}
        primary=Model();verified=Model();operations=Operations();operations.gemini=primary
        stages=PreparationStages('/unused',operations,lambda:None,narrative_model=verified)
        result=stages.research({'request':{'topic':'Topic','language':'ru','seconds':15}})
        self.assertEqual(verified.calls,['generation','independent-review'])
        self.assertEqual(primary.calls,[])
        self.assertIs(operations.gemini,primary)
        self.assertEqual(result['evidence'],evidence)


class MaterialInspectionModelRoutingTests(unittest.TestCase):
    def test_material_inspection_uses_confirmed_primary_multimodal_model(self):
        from hashlib import sha256
        from unittest.mock import patch
        from factory_next.preparation import PreparationStages

        source_text="The source documents claim one, claim two, and claim three."
        evidence={"sources":[{"id":"s1","url":"https://example.org/source",
                    "text":source_text,"sha256":sha256(source_text.encode()).hexdigest()}],
                  "facts":[{"id":f"f{i}","text":f"claim {word}",
                    "support":[{"source_id":"s1","quote":source_text}]}
                    for i,word in enumerate(("one","two","three"),1)]}
        request={"topic":"A documented subject","language":"en","seconds":15,
                 "visual_validation_mode":"gemini","required_fact_ids":["f1","f2","f3"]}
        source={"request":request,"evidence":evidence,"queries":[]}
        primary=SimpleNamespace(model="gemini-3.1-flash-lite")
        verified=SimpleNamespace(model="gemini-3.5-flash-lite")
        used_models=[]
        class Operations:
            def __init__(self):
                self.gemini=primary
            def discover(self,*args):
                return [{"id":f"photo-{i}"} for i in range(3)]
            def download(self,candidate):
                identity=candidate["id"]
                digest=sha256(identity.encode()).hexdigest()
                return {"id":identity,"sha256":digest,"media_type":"photo",
                        "visual_fingerprint":{"source_sha256":digest}}
            def inspect_many(self,batch,*args):
                used_models.append(self.gemini)
                return [{"asset_id":asset["id"]} for asset in batch]

        operations=Operations()
        stage=PreparationStages("/unused",operations,lambda:None,
                                narrative_model=verified)
        with patch("factory_next.preparation.validate_material"), \
             patch("factory_next.preparation.pixels"), \
             patch("factory_next.preparation.same_photo",return_value=False), \
             patch("factory_next.preparation.inspected_material",
                   side_effect=lambda asset,*args: {
                       "id":asset["id"],"sha256":asset["sha256"],
                       "supported_fact_ids":["f1","f2"]}):
            result=stage.materials({"outputs":{"research":source}})
        self.assertEqual(len(result["photos"]),3)
        self.assertEqual(len(used_models),1)
        self.assertIsNot(used_models[0],verified)
        self.assertEqual(used_models[0].model,"gemini-3.1-flash-lite")
        self.assertEqual(used_models[0].default_thinking_level,"medium")
        self.assertIsNot(used_models[0],primary)
        self.assertFalse(hasattr(primary,"default_thinking_level"))
        self.assertIs(operations.gemini,primary)


class MeasuredVariantTokenBudgetTests(unittest.TestCase):
    def test_initial_and_repair_generation_use_supported_16384_token_limit(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from factory_next.preparation import PreparationStages
        from factory_next.duration import NaturalDurationRejected

        scenes=[{"id":"scene-1","evidence_ids":["f1"],"narration":"Original sentence."}]
        selected=[{"id":"scene-1","evidence_ids":["f1"],"narration":"A revised sentence."}]
        evidence={"facts":[{"id":"f1","text":"A source fact."}]}
        request={"topic":"A test topic","language":"en","seconds":15,
                 "required_fact_ids":["f1"]}
        context={"outputs":{"research":{"request":request,"evidence":evidence},
                           "materials":{"photos":[{"id":"photo-1"}]},
                           "story":{"scenes":scenes,"script":"Original sentence."}}}
        class Model:
            def __init__(self):
                self.calls=object()
                self.generated=[]
            def generate(self,key,*args,**kwargs):
                self.generated.append((key,kwargs,args))
                return {},None
            def review_script(self,*args,**kwargs):
                return {"native_language_quality":True}
        model=Model()
        stage=PreparationStages("/unused",SimpleNamespace(gemini=model),
                                lambda:None,narrative_model=model)
        window={"min_words":20,"max_words":30,"target_words":25,
                "min_characters":80,"max_characters":110,"target_characters":95}
        with patch("factory_next.preparation.revision_length_window",return_value=window), \
             patch("factory_next.fact_allocation.allocate_scene_facts",return_value=scenes), \
             patch("factory_next.voice_variants.choose_variants",
                   side_effect=[NaturalDurationRejected("test repair path"),selected]), \
             patch("factory_next.voice_variants.variant_measurements",return_value={
                  "beat_1":{label:{"words":8,"characters":45}
                            for label in ("short","medium","long")}}), \
             patch("factory_next.preparation.validated_next_story",return_value=selected), \
             patch("factory_next.preparation.validate_native_surface"), \
             patch("factory_next.preparation.validate_script_review"):
            result=stage._revise_story_variants(context,15000)
        self.assertEqual(result["scenes"],selected)
        self.assertEqual([key for key,_,_ in model.generated],
                         ["next-measured-variants","next-measured-variants-repair"])
        self.assertEqual([kwargs.get("max_tokens") for _,kwargs,_ in model.generated],
                         [16384,16384])
        self.assertEqual([kwargs.get("thinking_level") for _,kwargs,_ in model.generated],
                         ["low","medium"])
        repair_data=model.generated[1][2][1]
        self.assertEqual(repair_data["duration_repair_diagnosis"]["classification"],
                         "all_variants_below_window")
        self.assertEqual(repair_data["duration_repair_diagnosis"][
                         "maximum_possible_total_characters"],45)
        self.assertIn("medium version from EVERY beat MUST contain",
                      model.generated[1][2][0])
        self.assertIn("medium narration must total 20-30 words",
                      model.generated[1][2][0])
        repair_schema=model.generated[1][2][2]
        for label in ("short","medium","long"):
            narration_schema=repair_schema["properties"]["beat_1"]["properties"][
                label]["properties"]["narration"]
            self.assertEqual(narration_schema.get("minLength"),1)
            self.assertEqual(narration_schema.get("maxLength"),2000)

 

class MeasuredSentenceRevisionRoutingTests(unittest.TestCase):
    def test_voice_fit_uses_verified_narrative_model_with_bounded_medium_reasoning(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from factory_next.preparation import PreparationStages

        original_scene={"id":"scene-1","material_id":"photo-1",
                        "evidence_ids":["f1"],"narration":"Original sentence."}
        revised=[{"id":"scene-1","material_id":"photo-1",
                  "evidence_ids":["f1"],"narration":"A reviewed revised sentence."}]
        evidence={"facts":[{"id":"f1","text":"A source fact."}]}
        request={"topic":"A test topic","language":"en","seconds":15,
                 "required_fact_ids":["f1"]}
        context={"outputs":{"research":{"request":request,"evidence":evidence},
                            "materials":{"photos":[{"id":"photo-1"}]},
                            "story":{"scenes":[original_scene],
                                     "script":"Original sentence."}}}
        class Model:
            def __init__(self):
                self.calls=object()
                self.default_thinking_level="high"
                self.generated=[]
                self.reviewed=[]
            def generate(self,key,*args,**kwargs):
                self.generated.append((key,args,kwargs))
                return {},None
            def review_script(self,data):
                self.reviewed.append(data)
                return {"native_language_quality":True}
        primary=Model(); verified=Model()
        stage=PreparationStages("/unused",SimpleNamespace(gemini=primary),
                                lambda:None,narrative_model=verified)
        window={"min_words":24,"max_words":32,"target_words":28,
                "min_characters":120,"max_characters":160,"target_characters":140}
        schema={"properties":{"beat_1":{"properties":{"sentence_1":{
            "minLength":1,"maxLength":160}}}}}
        with patch("factory_next.preparation.revision_length_window",return_value=window), \
             patch("factory_next.preparation.sentence_contract",return_value=(schema,[1])), \
             patch("factory_next.preparation.assemble_sentence_repair",return_value={"beats":revised}), \
             patch("factory_next.preparation.validated_next_story",return_value=revised), \
             patch("factory_next.preparation.validate_native_surface"), \
             patch("factory_next.preparation.validate_script_review"), \
             patch("factory_next.preparation.compact_materials",return_value=[]):
            result=stage.revise_story(context,15000)
        self.assertEqual(result["scenes"],revised)
        self.assertEqual(len(verified.generated),1)
        self.assertEqual(verified.generated[0][0],"next-measured-duration-revision")
        self.assertEqual(verified.generated[0][2].get("max_tokens"),16384)
        self.assertEqual(verified.generated[0][2].get("thinking_level"),"medium")
        self.assertEqual(len(verified.reviewed),1)
        self.assertEqual(primary.generated,[])
        self.assertEqual(primary.reviewed,[])
        self.assertEqual(primary.default_thinking_level,"high")
        self.assertEqual(verified.default_thinking_level,"high")
