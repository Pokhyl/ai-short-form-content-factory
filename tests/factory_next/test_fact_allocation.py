import unittest
from copy import deepcopy
from factory_next.fact_allocation import allocate_scene_facts

class FactAllocationTests(unittest.TestCase):
    def scenes(self, graph):
        return [{"material_id":str(i), "evidence_ids":row, "narration":"existing"}
                for i,row in enumerate(graph)]
    def test_duplicate_claims_are_distributed_without_losing_facts(self):
        original=self.scenes([["f1","f2"],["f1","f2"],["f3"]])
        saved=deepcopy(original)
        result=allocate_scene_facts(original)
        self.assertEqual([s["evidence_ids"] for s in result],[["f1"],["f2"],["f3"]])
        self.assertEqual(original,saved)
        self.assertEqual([s["material_id"] for s in result],["0","1","2"])
    def test_flexible_scene_cannot_steal_a_required_fact(self):
        result=allocate_scene_facts(self.scenes([["a","b"],["a"],["b","c"]]))
        self.assertEqual([s["evidence_ids"] for s in result],[["b"],["a"],["c"]])
    def test_all_nonessential_original_facts_remain_covered(self):
        result=allocate_scene_facts(self.scenes([["a","b","c"],["c","d"]]))
        flat=[f for s in result for f in s["evidence_ids"]]
        self.assertEqual(sorted(flat),["a","b","c","d"])
    def test_more_scenes_than_facts_keep_every_visual_beat(self):
        graph=[["a"],["a","b"],["b"],["a","b"]]
        result=allocate_scene_facts(self.scenes(graph))
        self.assertTrue(all(s["evidence_ids"] for s in result))
        for scene,allowed in zip(result,graph):
            self.assertLessEqual(set(scene["evidence_ids"]),set(allowed))
    def test_invalid_graph_rejects(self):
        for graph in ([],[[]],[["a","a"]],[["a"]]*9):
            with self.subTest(graph=graph),self.assertRaises(ValueError):
                allocate_scene_facts(self.scenes(graph))
    def test_unconnected_graph_preserves_eligibility(self):
        result=allocate_scene_facts(self.scenes([["a"],["a"],["b","c"],["d"]]))
        self.assertEqual(set(f for s in result for f in s["evidence_ids"]),set("abcd"))
        self.assertEqual(result[0]["evidence_ids"],["a"])
        self.assertEqual(result[1]["evidence_ids"],["a"])

    def test_all_three_fact_three_scene_graphs_have_minimum_citation_count(self):
        from itertools import combinations, product
        subsets=[list(c) for size in (1,2,3) for c in combinations("abc",size)]
        for graph in product(subsets,repeat=3):
            result=allocate_scene_facts(self.scenes(graph))
            all_facts=set(f for row in graph for f in row)
            maximum_matching=max(len(set(choice)) for choice in product(*graph))
            self.assertEqual(sum(len(s["evidence_ids"]) for s in result),
                             len(graph)+len(all_facts)-maximum_matching)
            self.assertEqual(set(f for s in result for f in s["evidence_ids"]),all_facts)
            for scene,allowed in zip(result,graph):
                self.assertTrue(scene["evidence_ids"])
                self.assertLessEqual(set(scene["evidence_ids"]),set(allowed))
