import unittest
from copy import deepcopy
from factory_next.voice_variants import choose_variants,variant_contract
from factory_next.duration import NaturalDurationRejected
class WholeVariantTests(unittest.TestCase):
 def setUp(self):
  self.scenes=[{"material_id":"image"+str(i),"evidence_ids":["fact"+str(i)]} for i in range(3)]
  self.reply={"beat_"+str(i+1):{
    "short":f"This is short complete sentence {i}.",
    "medium":f"This is a medium complete source sentence {i}.",
    "long":f"This is a longer complete source grounded sentence number {i}."}
    for i in range(3)}
  self.reply={beat:{label:{"fact_comparison":"Controlled exact fact coverage.","narration":text,"fact_ids":["fact"+str(i)]} for label,text in row.items()} for i,(beat,row) in enumerate(self.reply.items())}
 def window(self,text):
  return dict(target_words=len(text.split()),min_words=len(text.split()),max_words=len(text.split()),
              target_characters=len(text),min_characters=len(text),max_characters=len(text))
 def test_selects_mixed_whole_versions_and_preserves_exact_bindings(self):
  expected=[self.reply["beat_1"]["short"]["narration"],self.reply["beat_2"]["medium"]["narration"],self.reply["beat_3"]["long"]["narration"]]
  out=choose_variants(self.reply,self.scenes,self.window(" ".join(expected)))
  self.assertEqual(len(out["beats"]),3)
  for i,beat in enumerate(out["beats"]):
   self.assertIn(beat["narration"],[v["narration"] for v in self.reply["beat_"+str(i+1)].values()])
   self.assertEqual(beat["material_id"],"image"+str(i))
   self.assertEqual(beat["fact_ids"],["fact"+str(i)])
  self.assertEqual(len(" ".join(x["narration"] for x in out["beats"])),len(" ".join(expected)))
 def test_no_valid_combination_does_not_relax_total_window(self):
  with self.assertRaises(NaturalDurationRejected):
   choose_variants(self.reply,self.scenes,self.window("Five small words fit here."))
 def test_fragments_do_not_pass(self):
  reply={k:{label:{**value,"narration":"not a complete sentence here"} for label,value in row.items()} for k,row in self.reply.items()}
  with self.assertRaises(NaturalDurationRejected):choose_variants(reply,self.scenes,self.window(" ".join(row["short"]["narration"] for row in reply.values())))
 def test_unexpected_model_identity_is_rejected(self):
  reply=deepcopy(self.reply);reply["fact_ids"]=["fabricated"]
  with self.assertRaises(ValueError):choose_variants(reply,self.scenes,{})
 def test_repeated_sentences_across_beats_rejected(self):
  text="This is a repeated complete sentence."
  reply={k:{label:{**value,"narration":text} for label,value in row.items()} for k,row in self.reply.items()}
  with self.assertRaises(NaturalDurationRejected):choose_variants(reply,self.scenes,self.window(" ".join([text]*3)))
 def test_bounded_scene_count(self):
  with self.assertRaises(ValueError):variant_contract(self.scenes*3)

 def test_refined_citations_must_cover_all_original_facts(self):
  scenes=[{"material_id":"image0","evidence_ids":["fact0","fact1"]}]
  reply={"beat_1":self.reply["beat_1"]}
  with self.assertRaises(NaturalDurationRejected):
   choose_variants(reply,scenes,self.window(reply["beat_1"]["short"]["narration"]))
 def test_citation_cannot_introduce_unassigned_fact(self):
  reply=deepcopy(self.reply)
  reply["beat_1"]["short"]["fact_ids"]=["fabricated"]
  with self.assertRaises(ValueError):choose_variants(reply,self.scenes,{})
