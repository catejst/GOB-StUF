from unittest import TestCase
from unittest.mock import MagicMock, ANY

from gobstuf.stuf.brp.response.ingeschrevenpersonen import IngeschrevenpersonenStufResponse


class TestIngeschrevenpersonenStufResponse(TestCase):

    def test_get_links(self):
        res = IngeschrevenpersonenStufResponse(b'<xml></xml>')

        data = {}
        self.assertEqual(res.get_links(data), {})

        data = {
            'verblijfplaats': {
                'any attribute': 'any value'
            }
        }
        self.assertEqual(res.get_links(data), {})

        data = {
            'verblijfplaats': {
                'identificatiecodeNummeraanduiding': 'any nummeraanduiding'
            }
        }
        links = res.get_links(data)
        self.assertEqual(links, {'verblijfplaatsNummeraanduiding': {'href': ANY}})
        href = links['verblijfplaatsNummeraanduiding']['href']
        self.assertTrue('any nummeraanduiding' in href)
