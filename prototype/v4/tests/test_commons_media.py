from __future__ import annotations

import unittest

from prototype.v4.commons_media import parse_commons_response


def response(license_name='Public domain'):
    return {
        'query': {'pages': {'1': {
            'title': 'File:Example.jpg',
            'imageinfo': [{
                'url': 'https://upload.wikimedia.org/example.jpg',
                'thumburl': 'https://upload.wikimedia.org/thumb/example.jpg',
                'width': 3000,
                'height': 4000,
                'thumbwidth': 1080,
                'thumbheight': 1440,
                'mime': 'image/jpeg',
                'extmetadata': {
                    'LicenseShortName': {'value': license_name},
                    'LicenseUrl': {'value': 'https://license.example/'},
                    'Artist': {'value': '<b>Example Artist</b>'},
                    'Credit': {'value': 'Example credit'},
                    'ImageDescription': {'value': 'Exact subject'},
                },
            }],
        }}}
    }


class CommonsMediaTest(unittest.TestCase):
    def test_parses_free_asset_provenance(self):
        item = parse_commons_response(response(), requested_title='File:Example.jpg')
        self.assertEqual(item['orientation'], 'portrait')
        self.assertEqual(item['selected_width'], 1080)
        self.assertEqual(item['artist'], 'Example Artist')
        self.assertFalse(item['attribution_required'])

    def test_cc_by_requires_attribution(self):
        item = parse_commons_response(response('CC BY-SA 4.0'), requested_title='File:Example.jpg')
        self.assertTrue(item['attribution_required'])

    def test_unknown_license_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'license'):
            parse_commons_response(response('All Rights Reserved'), requested_title='File:Example.jpg')


if __name__ == '__main__':
    unittest.main()
