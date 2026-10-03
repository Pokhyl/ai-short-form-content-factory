import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("worker", "services/media-worker/server.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
fixture = json.loads(Path("tests/fixtures/m7-9802-alignment.json").read_text())
narration = " ".join(s["narration"] for s in fixture["scenes"])

short_scene_fixture = json.loads(Path("tests/fixtures/m7-short-terminal-scene.json").read_text())

class ShortTerminalSceneRegression(unittest.TestCase):
    def test_short_last_scene_is_fragile_under_one_whisper_word_error(self):
        scenes = short_scene_fixture["scenes"]
        narration = " ".join(scene["narration"] for scene in scenes)
        with self.assertRaisesRegex(ValueError, r"scene S9 lexical coverage below 0.85: 0.7917"):
            worker._build_scene_timings(narration, scenes, short_scene_fixture["whisper"], 29856)
        extended = json.loads(json.dumps(scenes))
        previous_words = extended[-2]["narration"].split()
        extended[-2]["narration"] = " ".join(previous_words[:-2])
        extended[-1]["narration"] = " ".join(previous_words[-2:]) + " " + extended[-1]["narration"]
        self.assertEqual(narration, " ".join(scene["narration"] for scene in extended))
        result = worker._build_scene_timings(narration, extended, short_scene_fixture["whisper"], 29856)
        self.assertGreaterEqual(result["scene_timings"][-1]["coverage"], 0.85)
        self.assertEqual(result["scene_timings"][-1]["end_ms"], 29856)

class SceneCutInsideWhisperTokenRegression(unittest.TestCase):
    def test_whisper_token_spanning_visual_cut_is_split_by_matched_characters(self):
        scenes = [
            {"scene_uuid": "00000000-0000-4000-8000-000000000001", "scene_key": "S1", "narration": "Барометр працює без"},
            {"scene_uuid": "00000000-0000-4000-8000-000000000002", "scene_key": "S2", "narration": "рідини і показує атмосферний тиск."},
        ]
        narration = " ".join(scene["narration"] for scene in scenes)
        words = [
            (" Барометр", 0, 500), (" працює", 500, 900),
            (" безрідини", 900, 1500), (" і", 1500, 1600),
            (" показує", 1600, 2200), (" атмосферний", 2200, 2800),
            (" тиск.", 2800, 3200),
        ]
        whisper = {"transcription": [{
            "text": "".join(word for word, _, _ in words),
            "tokens": [{"text": word, "offsets": {"from": start, "to": end}}
                       for word, start, end in words],
        }]}
        result = worker._build_scene_timings(narration, scenes, whisper, 3300)
        first, second = result["scene_timings"]
        self.assertEqual(first["end_ms"], 1100)
        self.assertEqual(second["start_ms"], 1100)
        self.assertEqual(second["end_ms"], 3200)
        self.assertEqual(result["global_coverage"], 1.0)

        ordinary = json.loads(json.dumps(whisper))
        ordinary_words = [
            (" Барометр", 0, 500), (" працює", 500, 900),
            (" без", 900, 1100), (" рідини", 1100, 1500),
            *words[3:],
        ]
        ordinary["transcription"][0]["text"] = "".join(word for word, _, _ in ordinary_words)
        ordinary["transcription"][0]["tokens"] = [
            {"text": word, "offsets": {"from": start, "to": end}}
            for word, start, end in ordinary_words
        ]
        unchanged = worker._build_scene_timings(narration, scenes, ordinary, 3300)
        self.assertEqual(unchanged["scene_timings"], result["scene_timings"])


class TrailingHallucinationRegression(unittest.TestCase):
    def test_saved_production_trailing_hallucination_preserves_all_scene_gates(self):
        saved = json.loads(Path("tests/fixtures/m7-trailing-asr-hallucination.json").read_text())
        narration = " ".join(scene["narration"] for scene in saved["scenes"])
        result = worker._build_scene_timings(
            narration, saved["scenes"], saved["whisper"], saved["audio_duration_ms"]
        )
        self.assertEqual(result["global_coverage"], 1.0)
        self.assertEqual(len(result["scene_timings"]), 9)
        self.assertTrue(all(scene["coverage"] == 1.0 for scene in result["scene_timings"]))
        self.assertEqual(result["lexical_end_ms_raw"], 29480)
        self.assertEqual(result["terminal_overrun_ms"], 0)

    def test_unmatched_trailing_music_does_not_create_terminal_overrun(self):
        scenes = [
            {
                "scene_uuid": "00000000-0000-4000-8000-000000000001",
                "scene_key": "S1",
                "narration": "Syfon działa.",
            },
        ]
        narration = scenes[0]["narration"]
        whisper = {
            "transcription": [
                {
                    "text": " Syfon działa.",
                    "tokens": [
                        {"text": " Syfon", "offsets": {"from": 0, "to": 500}},
                        {"text": " działa", "offsets": {"from": 500, "to": 900}},
                        {"text": ".", "offsets": {"from": 900, "to": 950}},
                    ],
                },
                {
                    "text": " [muzyka]",
                    "tokens": [
                        {"text": " [", "offsets": {"from": 1100, "to": 1150}},
                        {"text": "muzyka", "offsets": {"from": 1150, "to": 1900}},
                        {"text": "]", "offsets": {"from": 1900, "to": 2100}},
                    ],
                },
            ],
        }
        result = worker._build_scene_timings(narration, scenes, whisper, 1000)
        self.assertEqual(result["terminal_overrun_ms"], 0)
        self.assertEqual(result["lexical_end_ms_raw"], 900)
        self.assertEqual(result["scene_timings"][0]["end_ms"], 900)
        self.assertFalse(result["normalized_match"])

    def test_matched_narration_overrun_still_fails(self):
        scenes = [
            {
                "scene_uuid": "00000000-0000-4000-8000-000000000001",
                "scene_key": "S1",
                "narration": "Syfon działa.",
            },
        ]
        whisper = {
            "transcription": [{
                "text": " Syfon działa.",
                "tokens": [
                    {"text": " Syfon", "offsets": {"from": 0, "to": 500}},
                    {"text": " działa", "offsets": {"from": 500, "to": 2600}},
                    {"text": ".", "offsets": {"from": 2600, "to": 2650}},
                ],
            }],
        }
        with self.assertRaisesRegex(
            ValueError,
            "whisper lexical timing exceeds audio duration beyond tolerance",
        ):
            worker._build_scene_timings(
                scenes[0]["narration"], scenes, whisper, 1000
            )


class DtwRegression(unittest.TestCase):
    def test_saved_default_alignment_fails(self):
        with self.assertRaisesRegex(ValueError, "1614ms"):
            worker._build_scene_timings(narration, fixture["scenes"], fixture["whisper"], 14736)

    def test_saved_dtw_alignment_passes_existing_gates(self):
        payload = worker._dtw_timed_payload(fixture["dtw_whisper"], 14736)
        result = worker._build_scene_timings(narration, fixture["scenes"], payload, 14736)
        self.assertEqual(len(result["scene_timings"]), 5)
        self.assertEqual(result["terminal_overrun_ms"], 0)
        self.assertGreaterEqual(result["global_coverage"], 0.95)
        self.assertEqual(result["lexical_end_ms_raw"], 14380)
        self.assertEqual(fixture["dtw_whisper"]["transcription"][-1]["tokens"][0]["offsets"]["to"], 15460)

    def test_missing_dtw_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "no valid emission"):
            worker._dtw_timed_payload(fixture["whisper"], 14736)

    def test_invalid_dtw_is_not_clamped(self):
        for value in [2000, -1]:
            payload = json.loads(json.dumps(fixture["dtw_whisper"]))
            payload["transcription"][-1]["tokens"][0]["t_dtw"] = value
            with self.assertRaises(ValueError):
                worker._dtw_timed_payload(payload, 14736)


# End-to-end orchestration is exercised separately below through unittest discovery.
class DtwOrchestration(unittest.TestCase):
    def test_one_bounded_retry_on_exact_audio(self):
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "whisper.json").write_text(json.dumps(fixture["whisper"]))
            def fake_run(command, **kwargs):
                if "-dtw" in command:
                    (directory / "whisper-dtw.json").write_text(json.dumps(fixture["dtw_whisper"]))
            with patch.object(worker, "WHISPER_CLI", Path(__file__)), patch.object(worker, "whisper_model_sha256"), patch.object(worker.subprocess, "run", side_effect=fake_run) as run:
                payload, result = worker.run_local_alignment(Path("/exact.mp3"), "en", narration, fixture["scenes"], 14736, directory)
            self.assertEqual(run.call_count, 3)  # decode WAV, standard ASR, one DTW retry
            self.assertEqual(result["timing_source"], "dtw_emission_intervals")
            self.assertIn("standard_pass", payload)
            self.assertEqual(result["terminal_overrun_ms"], 0)




    def test_retry_ignores_non_speech_annotation_only_difference(self):
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            standard = json.loads(json.dumps(fixture["whisper"]))
            standard["transcription"].append({
                "text": " [music]",
                "tokens": [
                    {"text": " [", "offsets": {"from": 16200, "to": 16200}},
                    {"text": "music", "offsets": {"from": 16200, "to": 16300}},
                    {"text": "]", "offsets": {"from": 16300, "to": 16350}},
                ],
            })
            (directory / "whisper.json").write_text(json.dumps(standard))
            def fake_run(command, **kwargs):
                if "-dtw" in command:
                    (directory / "whisper-dtw.json").write_text(json.dumps(fixture["dtw_whisper"]))
            with patch.object(worker, "WHISPER_CLI", Path(__file__)), patch.object(worker, "whisper_model_sha256"), patch.object(worker.subprocess, "run", side_effect=fake_run):
                payload, result = worker.run_local_alignment(Path("/exact.mp3"), "en", narration, fixture["scenes"], 14736, directory)
            self.assertEqual(result["timing_source"], "dtw_emission_intervals")
            self.assertIn("standard_pass", payload)



    def test_retry_allows_tiny_same_audio_decoder_variance(self):
        self.assertTrue(worker.recognized_transcripts_consistent(
            "Сосуд Дьюара сохраняет температуру. [музыка]",
            "Сосуд диор сохраняет температуру.",
        ))

    def test_retry_rejects_material_transcript_change(self):
        self.assertFalse(worker.recognized_transcripts_consistent(
            "The pump moves water through the pipe.",
            "The turbine invents extra words in the scene.",
        ))

    def test_retry_still_rejects_real_lexical_change_after_annotation_normalization(self):
        left = worker.normalize_recognized_speech("The pump moves water. [music]")
        right = worker.normalize_recognized_speech("The turbine moves water.")
        self.assertNotEqual(left, right)

    def test_valid_default_alignment_does_not_retry(self):
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            passing = worker._dtw_timed_payload(fixture["dtw_whisper"], 14736)
            (directory / "whisper.json").write_text(json.dumps(passing))
            with patch.object(worker, "WHISPER_CLI", Path(__file__)), patch.object(worker, "whisper_model_sha256"), patch.object(worker.subprocess, "run") as run:
                _, result = worker.run_local_alignment(Path("/exact.mp3"), "en", narration, fixture["scenes"], 14736, directory)
            self.assertEqual(run.call_count, 2)
            self.assertNotIn("standard_timing_failure", result)

    def test_retry_cannot_change_recognized_words(self):
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "whisper.json").write_text(json.dumps(fixture["whisper"]))
            changed = json.loads(json.dumps(fixture["dtw_whisper"]))
            changed["transcription"][-1]["text"] = " invented extra words"
            def fake_run(command, **kwargs):
                if "-dtw" in command:
                    (directory / "whisper-dtw.json").write_text(json.dumps(changed))
            with patch.object(worker, "WHISPER_CLI", Path(__file__)), patch.object(worker, "whisper_model_sha256"), patch.object(worker.subprocess, "run", side_effect=fake_run):
                with self.assertRaisesRegex(ValueError, "changed the recognized transcript"):
                    worker.run_local_alignment(Path("/exact.mp3"), "en", narration, fixture["scenes"], 14736, directory)




class AlignmentNumberNormalization(unittest.TestCase):
    def test_century_ordinals_match_uppercase_roman_asr_across_languages(self):
        pairs = [
            ("in the seventeenth century", "in the XVII century"),
            ("w siedemnastym wieku", "w XVII wieku"),
            ("в семнадцатом веке", "в XVII веке"),
            ("у сімнадцятому столітті", "у XVII столітті"),
        ]
        for expected, asr in pairs:
            self.assertEqual(
                worker.normalize_alignment_text(expected),
                worker.normalize_alignment_text(asr),
            )

    def test_single_english_i_is_not_treated_as_roman_one(self):
        self.assertEqual(
            worker.normalize_alignment_text("I work"),
            "iwork",
        )

if __name__ == "__main__":
    unittest.main()
