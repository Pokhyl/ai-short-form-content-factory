"""Restore server-owned model identity across a materials stage restart."""
import unittest
from unittest.mock import Mock
from factory_next.preparation import PreparationStages
from factory_v3.grounding import validate_evidence


class MaterialsRestartTests(unittest.TestCase):
    def test_saved_gemini_photo_inspection_identity_survives_fresh_adapter(self):
        from unittest.mock import patch
        from material_first.operations import Operations
        from factory_v3.preflight import digest

        source_text="Andromeda is an observable spiral galaxy."
        from hashlib import sha256
        evidence={"sources":[{"id":"source-1","url":"https://example.org/andromeda",
                             "text":source_text,"sha256":sha256(source_text.encode()).hexdigest()}],
                  "facts":[{"id":"f1","text":"Andromeda is an observable spiral galaxy.",
                            "support":[{"source_id":"source-1","quote":source_text}]}]}
        source={"request":{"topic":"Andromeda Galaxy","language":"en","seconds":45,
                           "visual_validation_mode":"gemini","required_fact_ids":["f1"]},
                "evidence":evidence,"queries":[{"query":"Andromeda Galaxy"}]}
        sha="a"*64
        asset={"id":"original-photo","sha256":sha,"media_type":"photo",
               "source_url":"https://example.org/photo","author":"test","license":"CC0",
               "visual_fingerprint":{"source_sha256":sha}}
        candidate={"id":"original-photo"}
        class StopBeforeAnyProviderSend(Exception):
            pass

        identities=[]
        for previous_topic in ("Andromeda Galaxy","unrelated previous topic"):
            model=Mock()
            def capture(key,instruction,context,schema,**kwargs):
                identities.append(digest({"key":key,"instruction":instruction,
                    "context":context,"schema":schema,
                    "photo_ids":[p["asset_id"] for p in kwargs["photos"]]}))
                raise StopBeforeAnyProviderSend()
            model.generate.side_effect=capture
            operations=Operations("/no-real-files",None,model,None,None)
            operations.topic=previous_topic
            operations.discover=Mock(return_value=[candidate])
            operations.download=Mock(return_value=asset)
            operations._photo=Mock(return_value={"bytes":b"not-sent","mime":"image/jpeg",
                                                  "asset_id":"original-photo"})
            stage=PreparationStages("/no-real-files",operations,lambda:None)
            with patch("factory_next.preparation.validate_material"), \
                 patch("factory_next.preparation.pixels"):
                with self.assertRaises(StopBeforeAnyProviderSend):
                    stage.materials({"outputs":{"research":source}})
        self.assertEqual(len(identities),2)
        self.assertEqual(identities[0],identities[1])

    def test_restarted_operations_receive_original_topic_before_discovery(self):
        source_text="Andromeda is a spiral galaxy observed from Earth."
        from hashlib import sha256
        evidence={"sources":[{"id":"source-1","url":"https://example.org/andromeda",
                             "text":source_text,"sha256":sha256(source_text.encode()).hexdigest()}],
                  "facts":[{"id":"f1","text":"Andromeda is a spiral galaxy.",
                            "support":[{"source_id":"source-1","quote":source_text}]}]}
        validate_evidence(evidence)
        source={"request":{"topic":"Andromeda Galaxy","language":"en","seconds":45,
                           "visual_validation_mode":"gemini","required_fact_ids":["f1"]},
                "evidence":evidence,"queries":[{"query":"Andromeda Galaxy"}]}
        first=Mock()
        first.discover.return_value=[]
        original=PreparationStages("/unused",first,lambda:None)
        with self.assertRaisesRegex(ValueError,"insufficient distinct"):
            original.materials({"outputs":{"research":source}})
        self.assertEqual(first.topic,"Andromeda Galaxy")
        self.assertEqual(first.visual_validation_mode,"gemini")
        restarted=Mock()
        restarted.topic=None
        restarted.discover.return_value=[]
        resumed=PreparationStages("/unused",restarted,lambda:None)
        with self.assertRaisesRegex(ValueError,"insufficient distinct"):
            resumed.materials({"outputs":{"research":source}})
        self.assertEqual(restarted.topic,first.topic)
        self.assertEqual(restarted.visual_validation_mode,first.visual_validation_mode)
        self.assertEqual(restarted.discover.call_args,first.discover.call_args)


if __name__=="__main__":unittest.main()
