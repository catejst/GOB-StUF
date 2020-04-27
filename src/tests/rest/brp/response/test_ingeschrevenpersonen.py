from unittest import TestCase
from unittest.mock import MagicMock, ANY

from gobstuf.stuf.brp.response.ingeschrevenpersonen import IngeschrevenpersonenStufResponse


class TestIngeschrevenpersonenStufResponse(TestCase):

    def test_get_filtered_object(self):
        res = IngeschrevenpersonenStufResponse(b'<xml></xml>')

        obj = {}
        result = res.get_filtered_object(obj)
        self.assertEqual(result, {})

        obj = {'any key': 'any value'}
        result = res.get_filtered_object(obj)
        self.assertEqual(result, obj)

        res.inclusiefoverledenpersonen = False
        obj = {'any key': 'any value', 'overlijdensdatum': 'any datum'}
        result = res.get_filtered_object(obj)
        self.assertEqual(result, None)

        res.inclusiefoverledenpersonen = True
        result = res.get_filtered_object(obj)
        self.assertEqual(result, obj)

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
