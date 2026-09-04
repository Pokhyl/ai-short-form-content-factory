from __future__ import annotations

import unittest

from prototype.v4.caption_alignment import align_scene_caption_words


def w(start,end,text): return {'start':start,'end':end,'word':text}


class CaptionAlignmentTest(unittest.TestCase):
    def test_equal_count_uses_script_text_with_audio_timing(self):
        out=align_scene_caption_words('Выступ одного элемента', [w(0,0.3,'Выступ'),w(0.4,0.8,'подновой'),w(0.9,1.2,'элемента')])
        self.assertEqual([x['text'] for x in out],['Выступ','одного','элемента'])
        self.assertEqual(out[1]['startMs'],400)

    def test_two_script_words_can_share_one_recognized_timestamp(self):
        out=align_scene_caption_words('Na miejscu łączyli je nitami.', [w(0,0.2,'Na'),w(0.2,0.5,'miejscu'),w(0.5,0.9,'łączyli'),w(0.9,1.4,'jenitami.')])
        self.assertEqual([x['text'] for x in out],['Na','miejscu','łączyli','je nitami.'])
        self.assertEqual(out[-1]['startMs'],900)
        self.assertEqual(out[-1]['endMs'],1400)

    def test_collapsed_spoken_year_keeps_asr_digits_without_fake_word_times(self):
        out=align_scene_caption_words('w marcu tysiąc osiemset osiemdziesiątego dziewiątego roku.', [w(0,0.2,'w'),w(0.2,0.5,'marcu'),w(0.5,1.5,'1889'),w(1.5,1.9,'roku.')])
        self.assertEqual([x['text'] for x in out],['w','marcu','1889','roku.'])


if __name__=='__main__': unittest.main()
