import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("worker", "services/media-worker/server.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
fixture = json.loads(Path("tests/fixtures/m7-9802-alignment.json").read_text())
narration = " ".join(s["narration"] for s in fixture["scenes"])

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


if __name__ == "__main__":
    unittest.main()
