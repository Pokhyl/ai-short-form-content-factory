"""Real FFmpeg checks: terminal silence only, retained audio must be identical."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from factory_next.voice_tail import trim_terminal_silence


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
class VoiceTailTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def audio(self,speech,tail):
        source=self.root/'source.mp3'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i',f'sine=frequency=440:duration={speech}',
            '-af',f'apad=pad_dur={tail}','-ar','24000','-c:a','libmp3lame','-write_xing','0',str(source)],
            check=True,capture_output=True)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(source)]))
        return source,round(float(probe['format']['duration'])*1000)

    def test_removes_only_quiet_suffix_without_changing_original_or_retained_audio(self):
        source,ms=self.audio(14.6,.6);original=source.read_bytes()
        proof=trim_terminal_silence(source,self.root/'cut.mp3',ms,15)
        self.assertIsNotNone(proof)
        self.assertTrue(proof['exact_pcm_prefix'])
        self.assertLessEqual(proof['duration_ms'],15000)
        self.assertGreaterEqual(proof['duration_ms'],12900)
        self.assertEqual(source.read_bytes(),original)
        self.assertEqual(proof['original_sha256'],hashlib.sha256(original).hexdigest())

    def test_speech_at_cut_or_inside_guard_is_never_trimmed(self):
        for speech,tail in [(15.2,0),(14.9,.3)]:
            with self.subTest(speech=speech):
                source,ms=self.audio(speech,tail)
                self.assertIsNone(trim_terminal_silence(source,self.root/'cut.mp3',ms,15))
                source.unlink();(self.root/'cut.mp3').unlink(missing_ok=True)

    def test_large_overrun_or_underlength_does_not_touch_audio(self):
        for ms in (14000,15000,15751):
            self.assertIsNone(trim_terminal_silence(self.root/'absent',self.root/'cut',ms,15))
