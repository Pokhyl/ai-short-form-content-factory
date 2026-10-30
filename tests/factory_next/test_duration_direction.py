"""Saved real overshoot must not consume a third voice send with a longer draft."""
import json
from pathlib import Path
import unittest
from factory_next.duration import revision_length_window, revision_length_fits, duration_fits


class DurationDirectionTests(unittest.TestCase):
    def test_saved_wrong_direction_revision_is_rejected_before_tts(self):
        data=json.loads((Path(__file__).parent/'fixtures/actual-duration-c66597b7.json').read_text())
        scripts=[' '.join(s for row in draft.values() for s in row.values()) for draft in data['drafts']]
        self.assertGreater(len(scripts[1]),len(scripts[0]))
        old=revision_length_window(scripts[0],45096,45)
        self.assertTrue(revision_length_fits(scripts[1],old))
        new=revision_length_window(scripts[0],45096,45,centered=True)
        self.assertFalse(revision_length_fits(scripts[1],new))
        self.assertLess(new['max_characters'],len(scripts[0]))
        for key in ('min_characters','target_characters','max_characters'):
            self.assertTrue(duration_fits(new[key]/len(scripts[0])*45096,45))

    def test_all_supported_durations_languages_move_toward_interior(self):
        for seconds in (15,30,45,60):
            for word in ('water','woda','вода','лід'):
                script=(' '+word)*int(seconds*2)
                for measured in (seconds*1000+96,seconds*1000-3000):
                    with self.subTest(seconds=seconds,word=word,measured=measured):
                        win=revision_length_window(script,measured,seconds,centered=True)
                        self.assertLessEqual(win['min_characters'],win['max_characters'])
                        if measured>seconds*1000:self.assertLess(win['max_characters'],len(script))
                        else:self.assertGreater(win['min_characters'],len(script))
                        for key in ('min_characters','max_characters'):
                            self.assertTrue(duration_fits(win[key]/len(script)*measured,seconds))

    def test_audio_limits_remain_strict(self):
        self.assertFalse(duration_fits(45096,45))
        self.assertFalse(duration_fits(41400,45))
        self.assertFalse(duration_fits(47664,45))
        self.assertTrue(duration_fits(43950,45))

    def test_saved_complete_expansion_inside_audio_interval_is_not_overfiltered(self):
        root=Path(__file__).parent/'fixtures'
        source=json.loads((root/'actual-coverage-b89f1415.json').read_text())
        rows=json.loads((root/'actual-length-c90ef11b.json').read_text())
        text=' '.join(s for row in rows[1]['response'].values() for s in row.values())
        original=source['original']['script']
        win=revision_length_window(original,30504,45,centered=True)
        self.assertEqual(len(text),701)
        self.assertTrue(revision_length_fits(text,win))
        self.assertTrue(duration_fits(len(text)/len(original)*30504,45))
