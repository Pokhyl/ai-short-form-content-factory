"""Connected producer verification with explicitly synthetic provider/model decisions."""
import copy
import unittest
import test_catalog
from factory_v3.producer import Producer, select_previews
from factory_v3.catalog import CoverageUnavailable
from factory_v3.preflight import verify_before_voice


class Ledger:
    def __init__(self):
        self.claimed = False
        self.frozen = None
        self.rejected = None
    def claim_run(self, request_id):
        if self.frozen is not None:
            return {"cached": True, "frozen": self.frozen}
        if self.claimed:
            raise ValueError("run already claimed")
        self.claimed = True
        return {"cached": False, "request": {"topic": "controlled topic", "language": "pl", "seconds": 15}}
    def complete(self, request_id, frozen):
        self.frozen = frozen
    def reject(self, request_id, code):
        self.rejected = code


class ProducerTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_catalog.CatalogTests()
        self.fixture.setUp()
        self.ledger = Ledger()
        self.events = []
        f, events = self.fixture, self.events
        self.outline = {"evidence": f.evidence, "required_fact_ids": ["f"+str(i) for i in range(5)],
                        "units": copy.deepcopy(f.catalog["units"])}
        for i, unit in enumerate(self.outline["units"]):
            unit["queries"] = [{"query": "unit" + str(i) + " view" + str(j), "orientation": "portrait"} for j in range(3)]
        outer = self
        class Research:
            def fetch(self, *args):
                events.append("research")
                return f.evidence["sources"]
        class Gemini:
            def outline(self, request):
                events.append("outline")
                return outer.outline
            def review_photo(self, root, unit, asset, evidence):
                events.append("vision")
                return copy.deepcopy(next(r for r in f.catalog["reviews"] if r["scene_id"] == unit["id"]))
            def compose(self, request):
                events.append("compose")
                return f.compose(request)
            def review_script(self, request):
                events.append("script-review")
                return f.review_script(request)
        class Search:
            def search(self, provider, query, orientation):
                events.append("search")
                index = int(query[4])
                asset = dict(f.catalog["assets"][index], provider=provider)
                return {"receipt": {"controlled": True}, "candidates": [asset]}
        class Download:
            def download(self, candidate):
                events.append("download")
                return candidate
        self.producer = Producer(f.root, self.ledger, Research(), Gemini(), Search(), Download())

    def tearDown(self):
        self.fixture.tearDown()

    def test_connected_preparation_freezes_before_execution_and_replays_without_calls(self):
        frozen = self.producer.prepare("controlled")
        self.assertEqual(verify_before_voice(self.fixture.root, frozen)["topic"], "controlled topic")
        self.assertEqual(len(frozen["payload"]["selection"]), 5)
        self.assertLess(max(i for i,e in enumerate(self.events) if e == "vision"), self.events.index("compose"))
        self.assertEqual(self.events.count("compose"), 1)
        events = list(self.events)
        self.assertEqual(self.producer.prepare("controlled"), frozen)
        self.assertEqual(self.events, events)

    def test_missing_approved_media_blocks_composition_and_execution_job(self):
        self.fixture.catalog["reviews"][-1]["match_score"] = 0
        with self.assertRaises(CoverageUnavailable):
            self.producer.prepare("controlled")
        self.assertNotIn("compose", self.events)
        self.assertIsNone(self.ledger.frozen)
        self.assertEqual(self.ledger.rejected, "CoverageUnavailable")

    def test_three_preview_selection_covers_sources_and_queries(self):
        unit = self.outline["units"][0]
        pools = []
        for query_index in range(3):
            for provider in ["pixabay", "pexels", "wikimedia"]:
                pools.append({"query_index": query_index, "query": unit["queries"][query_index],
                    "result": {"receipt": {"controlled": provider}, "candidates": [{
                        "id": provider+str(query_index), "provider": provider, "description": "object"}]}})
        selected = select_previews(unit, pools)
        self.assertEqual(len(selected), 3)
        self.assertEqual(len({a["provider"] for a in selected}), 3)
        self.assertEqual(len({a["search_context"]["query_index"] for a in selected}), 3)
