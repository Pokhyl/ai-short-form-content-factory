from __future__ import annotations

import unittest

from prototype.v4.commons_media import parse_commons_response, parse_commons_search_response, _search_cache_key


def response(license_name='Public domain'):
    return {'query':{'pages':{'1':{'title':'File:Example.jpg','imageinfo':[{'url':'https://upload.wikimedia.org/example.jpg','thumburl':'https://upload.wikimedia.org/thumb/example.jpg','width':3000,'height':4000,'thumbwidth':1080,'thumbheight':1440,'mime':'image/jpeg','extmetadata':{'LicenseShortName':{'value':license_name},'LicenseUrl':{'value':'https://license.example/'},'Artist':{'value':'<b>Example Artist</b>'},'Credit':{'value':'Example credit'},'ImageDescription':{'value':'Exact subject'}}}]}}}}


class CommonsMediaTest(unittest.TestCase):
    def test_parses_free_asset_provenance(self):
        item=parse_commons_response(response(),requested_title='File:Example.jpg'); self.assertEqual(item['orientation'],'portrait'); self.assertEqual(item['selected_width'],1080); self.assertEqual(item['artist'],'Example Artist'); self.assertFalse(item['attribution_required'])
    def test_cc_by_requires_attribution(self):
        item=parse_commons_response(response('CC BY-SA 4.0'),requested_title='File:Example.jpg'); self.assertTrue(item['attribution_required'])
    def test_search_parser_filters_nonfree_candidates(self):
        free_page={'title':'File:Free diagram.svg','imageinfo':[{'url':'https://upload.wikimedia.org/free.svg','thumburl':'https://upload.wikimedia.org/free-1440.png','width':2000,'height':1200,'thumbwidth':1440,'thumbheight':864,'mime':'image/svg+xml','extmetadata':{'LicenseShortName':{'value':'CC BY-SA 4.0'},'Artist':{'value':'Example'}}}]}
        nonfree_page={'title':'File:Nonfree.jpg','imageinfo':[{'url':'https://example.test/x.jpg','width':1000,'height':800,'mime':'image/jpeg','extmetadata':{'LicenseShortName':{'value':'All rights reserved'}}}]}
        out=parse_commons_search_response({'query':{'pages':{'1':nonfree_page,'2':free_page}}}); self.assertEqual(len(out),1); self.assertEqual(out[0]['file_title'],'File:Free diagram.svg'); self.assertEqual(out[0]['license'],'CC BY-SA 4.0')
    def test_search_cache_key_is_deterministic_and_parameter_bound(self):
        a=_search_cache_key('OLED diagram',8,1440); b=_search_cache_key('OLED diagram',8,1440); c=_search_cache_key('OLED diagram',12,1440); self.assertEqual(a,b); self.assertNotEqual(a,c)
    def test_unknown_license_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'license'): parse_commons_response(response('All Rights Reserved'),requested_title='File:Example.jpg')

if __name__=='__main__': unittest.main()
