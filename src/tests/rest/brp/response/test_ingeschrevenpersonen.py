from unittest import TestCase
from unittest.mock import MagicMock, ANY

from gobstuf.stuf.brp.response.ingeschrevenpersonen import IngeschrevenpersonenStufResponse


class TestIngeschrevenpersonenStufResponse(TestCase):

    def empty_mapping(self, mapping):
        result = {}
        for k, v in mapping.items():
            if isinstance(v, dict):
                result[k] = self.empty_mapping(v)
            else:
                result[k] = None
        return result

    def test_get_filtered_object(self):
        res = IngeschrevenpersonenStufResponse(b'<xml></xml>')

        obj = self.empty_mapping(IngeschrevenpersonenStufResponse.mapping)
        result = res.get_filtered_object(obj)
        self.assertEqual(result, {})

        obj = self.empty_mapping(IngeschrevenpersonenStufResponse.mapping)
        obj['any key'] = 'any value'
        result = res.get_filtered_object(obj)
        self.assertEqual(result, {'any key': 'any value'})

        obj = self.empty_mapping(IngeschrevenpersonenStufResponse.mapping)
        obj['any key'] = 'any value'
        obj['overlijdensdatum'] = 'any datum'
        res.inclusiefoverledenpersonen = False
        result = res.get_filtered_object(obj)
        self.assertEqual(result, None)

        obj = self.empty_mapping(IngeschrevenpersonenStufResponse.mapping)
        obj['any key'] = 'any value'
        obj['overlijdensdatum'] = 'any datum'
        res.inclusiefoverledenpersonen = True
        result = res.get_filtered_object(obj)
        self.assertEqual(result, {'any key': 'any value', 'overlijdensdatum': 'any datum'})

        obj = self.empty_mapping(IngeschrevenpersonenStufResponse.mapping)
        obj['verblijfplaats']['woonadres'] = {'any key': 'any value'}
        result = res.get_filtered_object(obj)
        self.assertEqual(result, {'verblijfplaats': {'any key': 'any value', 'functieAdres': 'woonadres'}})

        obj = self.empty_mapping(IngeschrevenpersonenStufResponse.mapping)
        obj['verblijfplaats']['briefadres'] = {'any key': 'any value'}
        result = res.get_filtered_object(obj)
        self.assertEqual(result, {'verblijfplaats': {'any key': 'any value', 'functieAdres': 'briefadres'}})

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
