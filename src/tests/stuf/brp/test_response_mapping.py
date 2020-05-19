from unittest import TestCase
from unittest.mock import patch
from gobstuf.stuf.brp.response_mapping import Mapping, NPSMapping, StufObjectMapping, RelatedMapping, NPSNPSHUWMapping


class MappingImpl(Mapping):
    mapping = {}
    entity_type = 'TST'

class MappingImpl2(Mapping):
    mapping = {}
    entity_type = 'TST2'


class TestMapping(TestCase):

    def test_filter(self):
        mapping = MappingImpl()
        obj = {
            'any key': 'any value',
            'any null': None,
            'sub': {
                'any sub key': 'any sub value',
                'any sub null': None,
                'sub sub1': {
                    'any sub sub null': None
                },
                'sub sub2': {
                    'any sub sub': 'any sub sub value'
                }
            }
        }
        expect = {
            'any key': 'any value',
            'sub': {
                'any sub key': 'any sub value',
                'sub sub2': {
                    'any sub sub': 'any sub sub value'
                }
            }
        }

        # Default filtering is return all non null values
        self.assertEqual(mapping.filter(obj), expect)


class TestStufObjectMapping(TestCase):

    def test_register_and_get_for_entity_type(self):
        StufObjectMapping.register(MappingImpl)
        StufObjectMapping.register(MappingImpl2)

        self.assertIsInstance(StufObjectMapping.get_for_entity_type('TST'), MappingImpl)
        self.assertIsInstance(StufObjectMapping.get_for_entity_type('TST2'), MappingImpl2)

        # Should return different instances
        self.assertNotEqual(StufObjectMapping.get_for_entity_type('TST'),
                            StufObjectMapping.get_for_entity_type('TST'))

        with self.assertRaises(Exception):
            StufObjectMapping.get_for_entity_type('NONEXISTENT')


class TestNPSMapping(TestCase):

    def empty_mapping(self, mapping):
        result = {}
        for k, v in mapping.items():
            if isinstance(v, dict):
                result[k] = self.empty_mapping(v)
            else:
                result[k] = None
        return result

    def test_filter(self):
        mapping = NPSMapping()

        obj = self.empty_mapping(mapping.mapping)
        result = mapping.filter(obj)
        self.assertEqual(result, {})

        obj = self.empty_mapping(mapping.mapping)
        obj['any key'] = 'any value'
        result = mapping.filter(obj)
        self.assertEqual(result, {'any key': 'any value'})

        obj = self.empty_mapping(mapping.mapping)
        obj['any key'] = 'any value'
        obj['overlijdensdatum'] = 'any datum'
        kwargs = {'inclusiefoverledenpersonen': False}
        result = mapping.filter(obj, **kwargs)
        self.assertEqual(result, None)

        obj = self.empty_mapping(mapping.mapping)
        obj['any key'] = 'any value'
        obj['overlijdensdatum'] = 'any datum'
        kwargs = {'inclusiefoverledenpersonen': True}
        result = mapping.filter(obj, **kwargs)
        self.assertEqual(result, {'any key': 'any value', 'overlijdensdatum': 'any datum'})

        obj = self.empty_mapping(mapping.mapping)
        obj['verblijfplaats']['woonadres'] = {'any key': 'any value'}
        result = mapping.filter(obj)
        self.assertEqual(result, {'verblijfplaats': {'any key': 'any value', 'functieAdres': 'woonadres'}})

        obj = self.empty_mapping(mapping.mapping)
        obj['verblijfplaats']['briefadres'] = {'any key': 'any value'}
        result = mapping.filter(obj)
        self.assertEqual(result, {'verblijfplaats': {'any key': 'any value', 'functieAdres': 'briefadres'}})

    @patch("gobstuf.stuf.brp.response_mapping.request")
    @patch("gobstuf.stuf.brp.response_mapping.url_for", lambda name, **kwargs: f'/{name}/{kwargs["bsn"]}')
    def test_get_links(self, mock_request):
        mock_request.scheme = 'http(s)'
        mock_request.host = 'thishost'

        mapping = NPSMapping()
        mapped_object = {
            'verblijfplaats': {
                'woonadres': {
                    'identificatiecodeNummeraanduiding': '036digitdigitdigit'
                }
            },
            'burgerservicenummer': 'digitdigitdigit',
        }

        self.assertEqual({
            'verblijfplaatsNummeraanduiding': {
                'href': 'https://api.data.amsterdam.nl/gob/bag/nummeraanduidingen/036digitdigitdigit/',
            },
            'self': {
                'href': 'http(s)://thishost/brp_ingeschrevenpersonen_bsn/digitdigitdigit'
            }
        }, mapping.get_links(mapped_object))

        mapped_object = {}
        self.assertEqual({}, mapping.get_links(mapped_object))


class TestRelatedMapping(TestCase):

    def test_filter(self):
        class RelatedMappingImpl(RelatedMapping):
            entity_type = 'RELMAP'
            mapping = {'D': 'not important'}
            include_related = ['A', 'B']

        mapping = RelatedMappingImpl()
        mapped_object = {
            'A': 1,
            'B': 2,
            'C': 3,
            'D': 4,
        }

        # Assert that only the keys present in mapping and include_related are taken from mapped_object
        self.assertEqual({
            'A': 1,
            'B': 2,
            'D': 4,
        }, mapping.filter(mapped_object))


class TestNPSNPSHUWMapping(TestCase):

    @patch("gobstuf.stuf.brp.response_mapping.request")
    @patch("gobstuf.stuf.brp.response_mapping.url_for", lambda name, **kwargs: f'/{name}/{kwargs["bsn"]}')
    def test_get_links(self, mock_request):
        mock_request.scheme = 'http(s)'
        mock_request.host = 'thishost'

        mapping = NPSNPSHUWMapping()
        mapped_object = {
            'burgerservicenummer': 'digitdigitdigit',
        }

        self.assertEqual({
            'ingeschrevenPersoon': {
                'href': 'http(s)://thishost/brp_ingeschrevenpersonen_bsn/digitdigitdigit'
            }
        }, mapping.get_links(mapped_object))

        mapped_object = {}
        self.assertEqual({}, mapping.get_links(mapped_object))
