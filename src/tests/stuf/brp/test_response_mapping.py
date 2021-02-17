import freezegun

from unittest import TestCase
from unittest.mock import patch
from gobstuf.stuf.brp.response_mapping import (
    Mapping, NPSMapping, StufObjectMapping, RelatedMapping, NPSNPSHUWMapping, NPSNPSOUDMapping, NPSNPSKNDMapping, NPSFamilieRelatedMapping
)


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
            },
            'list': [
                {
                    'any sub key': 'any sub value',
                    'any sub null': None
                },
                {
                    'any sub null': None
                }
            ]
        }
        expect = {
            'any key': 'any value',
            'sub': {
                'any sub key': 'any sub value',
                'sub sub2': {
                    'any sub sub': 'any sub sub value'
                }
            },
            'list': [
                {
                    'any sub key': 'any sub value'
                }
            ]
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

    def test_sort_ouders(self):
        mapping = NPSMapping()

        def ensure_ordering(objects: list):
            ordered = mapping.sort_ouders(objects)
            order = [obj['order'] for obj in ordered]
            self.assertTrue(order == sorted(order))

            # Assert ouderAanduiding is assigned correctly
            self.assertTrue(all([ordered[idx]['ouderAanduiding'] == f'ouder{idx + 1}' for idx in range(len(ordered))]))

        ouders = [
            {
                'order': 3,
            },
            {
                'order': 2,
                'geboorte': {
                    'datum': {
                        'datum': '2000-06-01',
                    }
                }
            },
            {
                'order': 0,
                'geboorte': {
                    'datum': {
                        'datum': '2000-05',
                    }
                }
            },
            {
                'order': 1,
                'geboorte': {
                    'datum': {
                        'datum': '2000-05-01',
                    }
                }
            },
        ]
        # Test only geboortedatum
        ensure_ordering(ouders)

        ouders = [
            {
                'order': 1,
                'geslachtsaanduiding': 'man',
            },
            {
                'order': 0,
                'geslachtsaanduiding': 'vrouw',
            },
            {
                'order': 3,
            },
            {
                'order': 2,
                'geslachtsaanduiding': 'onbekend',
            },
        ]

        # Test only geslachtsaanduiding
        ensure_ordering(ouders)

        ouders = [
            {
                'order': 1,
                'naam': {
                    'geslachtsnaam': 'B'
                }
            },
            {
                'order': 3,
            },
            {
                'order': 2,
                'naam': {
                    'geslachtsnaam': 'Z'
                }
            },
            {
                'order': 0,
                'naam': {
                    'geslachtsnaam': 'A'
                }
            },
        ]
        # Test only geslachtsnaam
        ensure_ordering(ouders)

        ouders = [
            {
                'order': 1,
                'naam': {
                    'voornamen': 'B'
                }
            },
            {
                'order': 3,
            },
            {
                'order': 2,
                'naam': {
                    'voornamen': 'Z'
                }
            },
            {
                'order': 0,
                'naam': {
                    'voornamen': 'A'
                }
            },
        ]
        # Test only voornamen
        ensure_ordering(ouders)

        ouders = [
            {
                'order': 3,
                'geboorte': {
                    'datum': {
                        'datum': '2020-05-01',
                    }
                },
                'geslachtsaanduiding': 'man',
                'naam': {
                    'geslachtsnaam': 'B',
                    'voornamen': 'B',
                }
            },
            {
                # Vrouw first
                'order': 0,
                'geboorte': {
                    'datum': {
                        'datum': '2020-05-01',
                    }
                },
                'geslachtsaanduiding': 'vrouw',
            },
            {
                # First geslachtsnaam
                'order': 1,
                'geboorte': {
                    'datum': {
                        'datum': '2020-05-01',
                    }
                },
                'geslachtsaanduiding': 'man',
                'naam': {
                    'geslachtsnaam': 'A',
                }
            },
            {
                # First voornamen
                'order': 2,
                'geboorte': {
                    'datum': {
                        'datum': '2020-05-01',
                    }
                },
                'geslachtsaanduiding': 'man',
                'naam': {
                    'geslachtsnaam': 'B',
                    'voornamen': 'A',
                }
            },
            {
                # Oldest person
                'order': 4,
                'geboorte': {
                    'datum': {
                        'datum': '2020-06-01',
                    }
                }
            },

        ]
        # Test all together
        ensure_ordering(ouders)

    def test_sort_kinderen(self):
        mapping = NPSMapping()

        def ensure_ordering(objects: list):
            ordered = mapping.sort_kinderen(objects)
            order = [obj['order'] for obj in ordered]

            self.assertTrue(order == sorted(order))

        kinderen = [
            {
                'order': 3,
            },
            {
                'order': 2,
                'geboorte': {
                    'datum': {
                        'datum': '2000-06-01',
                    }
                }
            },
            {
                'order': 0,
                'geboorte': {
                    'datum': {
                        'datum': '2000-05',
                    }
                }
            },
            {
                'order': 1,
                'geboorte': {
                    'datum': {
                        'datum': '2000-05-01',
                    }
                }
            },
        ]
        # Test only geboortedatum
        ensure_ordering(kinderen)

        kinderen = [
            {
                'order': 1,
                'naam': {
                    'geslachtsnaam': 'B'
                }
            },
            {
                'order': 3,
            },
            {
                'order': 2,
                'naam': {
                    'geslachtsnaam': 'Z'
                }
            },
            {
                'order': 0,
                'naam': {
                    'geslachtsnaam': 'A'
                }
            },
        ]
        # Test only geslachtsnaam
        ensure_ordering(kinderen)

        kinderen = [
            {
                'order': 1,
                'naam': {
                    'voornamen': 'B'
                }
            },
            {
                'order': 3,
            },
            {
                'order': 2,
                'naam': {
                    'voornamen': 'Z'
                }
            },
            {
                'order': 0,
                'naam': {
                    'voornamen': 'A'
                }
            },
        ]
        # Test only voornamen
        ensure_ordering(kinderen)

        kinderen = [
            {
                'order': 3,
                'geboorte': {
                    'datum': {
                        'datum': '2020-05-01',
                    }
                },
                'naam': {
                    'geslachtsnaam': 'B',
                    'voornamen': 'B',
                }
            },
            {
                # First geslachtsnaam
                'order': 0,
                'geboorte': {
                    'datum': {
                        'datum': '2020-05-01',
                    }
                },
                'naam': {
                    'geslachtsnaam': 'A',
                }
            },
            {
                # First voornamen
                'order': 1,
                'geboorte': {
                    'datum': {
                        'datum': '2020-05-01',
                    }
                },
                'naam': {
                    'geslachtsnaam': 'B',
                    'voornamen': 'A',
                }
            },
            {
                # Oldest person
                'order': 3,
                'geboorte': {
                    'datum': {
                        'datum': '2020-06-01',
                    }
                }
            },

        ]
        # Test all together
        ensure_ordering(kinderen)

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
        obj['overlijden']['indicatieOverleden'] = True
        kwargs = {'inclusiefoverledenpersonen': False}
        result = mapping.filter(obj, **kwargs)
        self.assertEqual(result, None)

        obj = self.empty_mapping(mapping.mapping)
        obj['any key'] = 'any value'
        obj['overlijden']['indicatieOverleden'] = True
        kwargs = {'inclusiefoverledenpersonen': True}
        result = mapping.filter(obj, **kwargs)
        self.assertEqual(result, {'any key': 'any value', 'overlijden': {'indicatieOverleden': True}})

        obj = self.empty_mapping(mapping.mapping)
        obj['verblijfplaats']['woonadres'] = {'any key': 'any value'}
        result = mapping.filter(obj)
        self.assertEqual(result, {'verblijfplaats': {'any key': 'any value', 'functieAdres': 'woonadres'}})

        obj = self.empty_mapping(mapping.mapping)
        obj['verblijfplaats']['briefadres'] = {'any key': 'any value'}
        result = mapping.filter(obj)
        self.assertEqual(result, {'verblijfplaats': {'any key': 'any value', 'functieAdres': 'briefadres'}})

    @patch("gobstuf.stuf.brp.response_mapping.get_auth_url",
           lambda name, **kwargs: f"https://theurl/{name}/{kwargs['bsn']}/type/{kwargs.get('thetype_id', kwargs.get('theothertype_id'))}")
    def test_add_related_object_links(self):
        # _add_related_object_links is also indirectly tested by the test_get_links method below.
        # This method tests the method in isolation
        mapping = NPSMapping()
        mapped_object = {
            'burgerservicenummer': 'digitdigitdigit',
            '_embedded': {
                'thetype': [
                    {'burgerservicenummer': 'digitdigitdigit1'},
                    {'burgerservicenummer': 'digitdigitdigit2'},
                ]
            },
            '_links': {
                'thetype': [
                    {'burgerservicenummer': 'digitdigitdigit1'},
                    {'burgerservicenummer': 'digitdigitdigit2'},
                ],
                'theothertype': [
                    {'burgerservicenummer': 'digitdigitdigit3'},
                    {'burgerservicenummer': 'digitdigitdigit4'},
                ]
            }
        }
        links = {}

        mapping._add_related_object_links(mapped_object, links, 'thetype', 'theroute')

        self.assertEqual({
            'thetype': [
                {'href': 'https://theurl/theroute/digitdigitdigit/type/1'},
                {'href': 'https://theurl/theroute/digitdigitdigit/type/2'},
            ]
        }, links)

        self.assertEqual({
            '_embedded': {
                'thetype': [
                    {
                        '_links': {
                            'self': {
                                'href': 'https://theurl/theroute/digitdigitdigit/type/1'
                            }
                        },
                        'burgerservicenummer': 'digitdigitdigit1'
                    },
                    {
                        '_links': {
                            'self': {
                                'href': 'https://theurl/theroute/digitdigitdigit/type/2'
                            }
                        },
                        'burgerservicenummer': 'digitdigitdigit2'
                    }
                ]
            },
            '_links': {
                'thetype': [
                    {'burgerservicenummer': 'digitdigitdigit1'},
                    {'burgerservicenummer': 'digitdigitdigit2'},
                ],
                'theothertype': [
                    {'burgerservicenummer': 'digitdigitdigit3'},
                    {'burgerservicenummer': 'digitdigitdigit4'},
                ]
            },
            'burgerservicenummer': 'digitdigitdigit'
        }, mapped_object)

        # Should add 'theothertype' links as well, without having matching embedded objects
        mapping._add_related_object_links(mapped_object, links, 'theothertype', 'theroute')

        self.assertEqual({
            'thetype': [
                {'href': 'https://theurl/theroute/digitdigitdigit/type/1'},
                {'href': 'https://theurl/theroute/digitdigitdigit/type/2'},
            ],
            'theothertype': [
                {'href': 'https://theurl/theroute/digitdigitdigit/type/1'},
                {'href': 'https://theurl/theroute/digitdigitdigit/type/2'},
            ],
        }, links)


    @patch("gobstuf.stuf.brp.response_mapping.get_auth_url",
           lambda name, **kwargs: f'http(s)://thishost/{name}/{kwargs["bsn"]}')
    def test_get_links(self):

        mapping = NPSMapping()
        mapped_object = {
            'verblijfplaats': {
                'woonadres': {
                    'identificatiecodeNummeraanduiding': '036digitdigitdigit'
                }
            },
            'burgerservicenummer': 'digitdigitdigit',
            '_embedded': {
                'partners': [
                    {'burgerservicenummer': 'digitdigitdigit1'},
                    {'burgerservicenummer': 'digitdigitdigit2'}
                ]
            },
            '_links': {
                'partners': [
                    {'burgerservicenummer': 'digitdigitdigit1'},
                    {'burgerservicenummer': 'digitdigitdigit2'},
                ]
            },
        }

        self.assertEqual({
            'verblijfplaatsNummeraanduiding': {
                'href': 'https://api.data.amsterdam.nl/gob/bag/nummeraanduidingen/036digitdigitdigit/',
            },
            'self': {
                'href': 'http(s)://thishost/brp_ingeschrevenpersonen_bsn/digitdigitdigit'
            },
            'partners': [
                {'href': 'http(s)://thishost/brp_ingeschrevenpersonen_bsn_partners_detail/digitdigitdigit'},
                {'href': 'http(s)://thishost/brp_ingeschrevenpersonen_bsn_partners_detail/digitdigitdigit'}
            ]
        }, mapping.get_links(mapped_object))

        for c, partner in enumerate(mapped_object['_embedded']['partners']):
            self.assertEqual(partner['_links']['self']['href'],
                             'http(s)://thishost/brp_ingeschrevenpersonen_bsn_partners_detail/digitdigitdigit')

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

    @patch("gobstuf.stuf.brp.response_mapping.get_auth_url",
           lambda name, **kwargs: f'http(s)://thishost/{name}/{kwargs["bsn"]}')
    def test_get_links(self):
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

    def test_filter(self):
        mapping = NPSNPSHUWMapping()

        expected = {
            'burgerservicenummer': 'bsn val',
            'geboorte': 'geboorte fields',
            'naam': 'naam fields',
            'aangaanHuwelijkPartnerschap': 'some date'
        }
        mapped_object = {
            'datumOntbinding': None,
            'someFilteredOutField': 'its value',
            **expected
        }
        self.assertEqual(expected, mapping.filter(mapped_object))

        # Has datumOntbinding. Object is filtered out.
        mapped_object = {
            'datumOntbinding': 'some date',
            **expected,
        }
        self.assertIsNone(mapping.filter(mapped_object))


class TestNPSFamilieRelatedMapping(TestCase):

    class NPSFamilieRelatedMappingImpl(NPSFamilieRelatedMapping):

        @property
        def entity_type(self):
            return 'ImplEntityType'

    @patch("gobstuf.stuf.brp.response_mapping.get_auth_url",
           lambda name, **kwargs: f'http(s)://thishost/{name}/{kwargs["bsn"]}')
    def test_get_links(self):
        mapping = self.NPSFamilieRelatedMappingImpl()
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

    def test_filter(self):
        mapping = self.NPSFamilieRelatedMappingImpl()

        keys = [
            'aanduidingStrijdigheidNietigheid',
            'datumIngangFamilierechtelijkeBetrekkingRaw',
            'datumEindeFamilierechtelijkeBetrekking'
        ]
        # Assert the necessary keys are present in mapping. Filter relies on these keys.
        self.assertTrue(all([key in mapping.mapping for key in keys]))

        self.assertIsNone(mapping.filter({'aanduidingStrijdigheidNietigheid': 'true'}))

        with freezegun.freeze_time('20200831'):
            self.assertIsNone(mapping.filter({'datumIngangFamilierechtelijkeBetrekkingRaw': '20200901'}))
            self.assertIsNone(mapping.filter({'datumEindeFamilierechtelijkeBetrekking': '20200830'}))

        self.assertIsNone(mapping.filter({'naam': {}}))
        self.assertIsNotNone(mapping.filter({'naam': {'voornamen': 'Voornaam'}}))
        self.assertIsNotNone(mapping.filter({'naam': {'geslachtsnaam': 'Geslachtsnaam'}}))
        self.assertIsNotNone(mapping.filter({'geboorte': {'some': 'thing'}}))

        with freezegun.freeze_time('20200831'):
            obj = {
                'aanduidingStrijdigheidNietigheid': 'not true',
                'datumIngangFamilierechtelijkeBetrekkingRaw': '202008',  # Smaller precision, should work
                'datumEindeFamilierechtelijkeBetrekking': '202009',  # Smaller precision, should work
                'naam': {
                    'voornamen': 'Voornaam',
                }
            }
            res = mapping.filter(obj)

            deleted_keys = [
                'aanduidingStrijdigheidNietigheid',
                'datumIngangFamilierechtelijkeBetrekkingRaw',
                'datumEindeFamilierechtelijkeBetrekking'
            ]

            self.assertTrue(all([key not in res for key in deleted_keys]))


class TestNPSNPSOUDMapping(TestCase):

    def test_entity_type(self):
        mapping = NPSNPSOUDMapping()
        self.assertEqual('NPSNPSOUD', mapping.entity_type)

    def test_include_related(self):
        mapping = NPSNPSOUDMapping()
        self.assertEqual([
            'burgerservicenummer',
            'naam',
            'geboorte',
            'geheimhoudingPersoonsgegevens',
            'geslachtsaanduiding',
        ], mapping.include_related)

    def test_mapping(self):
        self.assertEqual([
            'aanduidingStrijdigheidNietigheid',
            'datumIngangFamilierechtelijkeBetrekking',
            'datumIngangFamilierechtelijkeBetrekkingRaw',
            'datumEindeFamilierechtelijkeBetrekking',
            'ouderAanduiding',
        ], list(NPSNPSOUDMapping().mapping.keys()))


class TestNPSNPSKNDMapping(TestCase):

    def test_entity_type(self):
        mapping = NPSNPSKNDMapping()
        self.assertEqual('NPSNPSKND', mapping.entity_type)

    def test_include_related(self):
        mapping = NPSNPSKNDMapping()

        # Test that parent attrs are included
        self.assertEqual([
            'burgerservicenummer',
            'naam',
            'geboorte',
            'geheimhoudingPersoonsgegevens',
            'leeftijd',
        ], mapping.include_related)
