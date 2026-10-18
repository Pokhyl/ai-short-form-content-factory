"""Offline real-FFmpeg contract: 43.656-second speech produces a 45s audited MP4."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from factory_next.duration import duration_fits
from material_first.presentation import TOPIC_POLICY, render_whole_photos, visual_timeline
from material_first.qa import audit_whole
from material_first.rendering import probe, sha

@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "requires ffmpeg and ffprobe")
class NaturalTailMediaTests(unittest.TestCase):
    def test_full_render_and_independent_byte_audit_preserve_43_second_voice(self):
        with tempfile.TemporaryDirectory(prefix="factory-next-natural-tail-") as folder:
            root=Path(folder)
            job=str(uuid4())
            voice=root/"voiceovers"/job/"final.mp3"
            voice.parent.mkdir(parents=True)
            # Real local MP3; provider calls, quotas and user material untouched.
            subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","lavfi",
                "-i","sine=frequency=440:duration=43.63",
                "-ar","48000","-ac","1","-c:a","libmp3lame","-q:a","4",
                str(voice)],check=True,timeout=25)
            measured=round(float(probe(voice)["format"]["duration"])*1000)
            self.assertTrue(43000<=measured<44000)
            self.assertTrue(duration_fits(measured,45))
            images=[]
            for i in range(9):
                path=root/f"image-{i}.png"
                colour=f"0x{25+i*18:02x}{60+i*9:02x}{110+i*7:02x}"
                subprocess.run(["ffmpeg","-nostdin","-v","error","-y",
                    "-f","lavfi","-i",f"color=c={colour}:s=400x640",
                    "-frames:v","1","-update","1",str(path)],check=True,timeout=10)
                images.append(path)
            timeline=visual_timeline(45,9,TOPIC_POLICY)
            rendered=root/"renders"/job
            proof=render_whole_photos(rendered,voice,images,45,
                                      policy=TOPIC_POLICY,timeline=timeline)
            self.assertEqual(proof["source_audio_duration_ms"],measured)
            self.assertEqual(proof["actual_duration_ms"],45000)
            self.assertEqual(proof["audio_tempo_factor"],1.0)
            self.assertEqual(proof["new_tts_calls"],0)
            voice_hash=sha(voice)
            manifest={
                "sha256":proof["video_sha256"],
                "input_audio_sha256":voice_hash,
                "fitted_audio_sha256":proof["fitted_audio_sha256"],
                "audio_duration_ms":measured,"audio_tempo_factor":1.0,
                "duration_policy":TOPIC_POLICY,
                "segments":[
                    {"asset_path":str(photo),"asset_sha256":sha(photo),
                     **cut}
                    for photo,cut in zip(images,timeline)],
            }
            (rendered/"manifest.json").write_text(json.dumps(manifest))
            payload={"seconds":45,"presentation_policy":TOPIC_POLICY,
                     "visuals":[{"material_id":str(i)} for i in range(9)],
                     "assets":[{"sha256":sha(path)} for path in images]}
            result=audit_whole(root,job,payload,proof["video_sha256"],voice_hash,
                timings=[{"start_ms":0,"end_ms":measured}])
            self.assertTrue(result["passed"])
            self.assertTrue(all(result["gates"].values()))
            self.assertEqual(result["duration_ms"],45000)
            self.assertEqual(result["scene_count"],9)


if __name__=="__main__":
    unittest.main()
