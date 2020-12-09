from unittest import TestCase
from unittest.mock import patch

import datetime

from gobstuf.mks_utils import MKSConverter, _today, DataItemNotFoundException
from gobstuf.indications import Indication


class TestMKSConverter(TestCase):

    def test_is_mks_datum(self):
        self.assertTrue(MKSConverter._is_mks_datum("20200422"))
        self.assertFalse(MKSConverter._is_mks_datum("2020042"))
        self.assertFalse(MKSConverter._is_mks_datum("202004221"))
        self.assertFalse(MKSConverter._is_mks_datum(None))
        self.assertFalse(MKSConverter._is_mks_datum(""))
        self.assertFalse(MKSConverter._is_mks_datum("yyyymmdd"))

    def test_yyyy(self):
        self.assertEqual(MKSConverter._yyyy("20200422"), "2020")
        self.assertEqual(MKSConverter._yyyy("202004221"), None)

    def test_mm(self):
        self.assertEqual(MKSConverter._mm("20200422"), "04")
        self.assertEqual(MKSConverter._mm("202004221"), None)

    def test_dd(self):
        self.assertEqual(MKSConverter._dd("20200422"), "22")
        self.assertEqual(MKSConverter._dd("202004221"), None)

    def test_as_datum(self):
        self.assertEqual(MKSConverter.as_datum("20200422"), "2020-04-22")
        self.assertEqual(MKSConverter.as_datum("202004221"), None)

    def test_as_datum_broken_down(self):
        self.assertEqual(MKSConverter.as_datum_broken_down("20200422"), {
            'datum': '2020-04-22',
            'jaar': 2020,
            'maand': 4,
            'dag': 22})
        self.assertEqual(MKSConverter.as_datum_broken_down("202004221"), None)

    def test_as_jaar(self):
        self.assertEqual(MKSConverter.as_jaar("20200422"), 2020)
        self.assertEqual(MKSConverter.as_jaar("202004221"), None)

    def test_as_maand(self):
        self.assertEqual(MKSConverter.as_maand("20200422"), 4)
        self.assertEqual(MKSConverter.as_maand("202004221"), None)

    def test_as_dag(self):
        self.assertEqual(MKSConverter.as_dag("20200422"), 22)
        self.assertEqual(MKSConverter.as_dag("202004221"), None)

    def test_as_code(self):
        for length in range(1, 5):
            as_code = MKSConverter.as_code(length)
            code = as_code("1")
            self.assertEqual(len(code), length)

        as_code = MKSConverter.as_code(4)
        self.assertIsNone(as_code(None))

    @patch('gobstuf.mks_utils.CodeResolver')
    def test_get_gemeente_code(self, mock_code_resolver):
        mock_code_resolver.get_gemeente_code.return_value = 'any code'
        self.assertEqual(MKSConverter.get_gemeente_code("any omschrijving"), 'any code')

    @patch('gobstuf.mks_utils.CodeResolver')
    def test_as_gemeente_code(self, mock_code_resolver):
        # Case in which the gemeente_code is known. Return padded gemeente_code
        mock_code_resolver.get_gemeente.return_value = 'any gemeente'
        self.assertEqual(MKSConverter.as_gemeente_code('363'), '0363')

        # Gemeente_code is not known, return None (code will be set in gemeente omschrijving)
        mock_code_resolver.get_gemeente.side_effect = DataItemNotFoundException
        self.assertEqual(MKSConverter.as_gemeente_code('363'), None)

    @patch('gobstuf.mks_utils.CodeResolver')
    def test_get_gemeente_omschrijving(self, mock_code_resolver):
        mock_code_resolver.get_gemeente.return_value = 'any omschrijving'
        self.assertEqual(MKSConverter.get_gemeente_omschrijving("any gemeente"), 'any omschrijving')

        # If gemeente is not found, return code as omschrijving
        mock_code_resolver.get_gemeente.side_effect = DataItemNotFoundException
        self.assertEqual(MKSConverter.get_gemeente_omschrijving("any gemeente"), 'any gemeente')

    @patch('gobstuf.mks_utils.CodeResolver')
    def test_get_land_omschrijving(self, mock_code_resolver):
        mock_code_resolver.get_land.return_value = 'any omschrijving'
        self.assertEqual(MKSConverter.get_land_omschrijving("any land"), 'any omschrijving')

    def test_today(self):
        today = _today()
        self.assertIsInstance(today, datetime.date)

    @patch('gobstuf.mks_utils._today')
    def test_as_leeftijd(self, mock_today):
        mock_today.return_value = datetime.date(2020, 4, 22)
        self.assertEqual(MKSConverter.as_leeftijd("20200422"), 0)
        self.assertEqual(MKSConverter.as_leeftijd("20190423"), 0)
        self.assertEqual(MKSConverter.as_leeftijd("20190422"), 1)
        self.assertEqual(MKSConverter.as_leeftijd("20190421"), 1)

        # https://github.com/VNG-Realisatie/Haal-Centraal-BRP-bevragen/blob/master/features/leeftijd_bepaling.feature

        # Volledig geboortedatum
        birthday = "19830526"
        mock_today.return_value = datetime.date(2019, 5, 26)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), 36)
        mock_today.return_value = datetime.date(2019, 11, 30)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), 36)
        mock_today.return_value = datetime.date(2019, 1, 1)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), 35)

        # Jaar en maand van geboorte datum zijn bekend
        birthday = "19830515"
        mock_today.return_value = datetime.date(2019, 5, 31)
        self.assertEqual(MKSConverter.as_leeftijd(birthday, ind_onvolledige_datum='D'), None)
        mock_today.return_value = datetime.date(2019, 6, 1)
        self.assertEqual(MKSConverter.as_leeftijd(birthday, ind_onvolledige_datum='D'), 36)
        mock_today.return_value = datetime.date(2019, 4, 30)
        self.assertEqual(MKSConverter.as_leeftijd(birthday, ind_onvolledige_datum='D'), 35)

        # Alleen jaar van geboorte datum is bekend
        birthday = "19830515"
        mock_today.return_value = datetime.date(2019, 5, 31)
        self.assertEqual(MKSConverter.as_leeftijd(birthday, ind_onvolledige_datum='M'), None)

        # Persoon is overleden
        birthday = "19830526"
        mock_today.return_value = datetime.date(2019, 5, 26)
        self.assertEqual(MKSConverter.as_leeftijd(birthday, overlijdensdatum="20000101"), None)

        # Volledig onbekend geboortedatum
        birthday = "19830526"
        mock_today.return_value = datetime.date(2019, 5, 26)
        self.assertEqual(MKSConverter.as_leeftijd(birthday, ind_onvolledige_datum='J2'), None)
        self.assertEqual(MKSConverter.as_leeftijd(None), None)

        # Geboren op 29 februari in een schrikkeljaar
        birthday = "19960229"
        mock_today.return_value = datetime.date(2016, 2, 29)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), 20)
        mock_today.return_value = datetime.date(2017, 2, 28)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), 20)
        mock_today.return_value = datetime.date(2017, 3, 1)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), 21)

    def test_indication(self):
        class AnyIndication(Indication):

            @property
            def indications(self):
                return {
                    'a': 'b',
                    'c': 'd'
                }

        indication = AnyIndication()
        self.assertEqual(indication.identifiers, {
            'b': 'a',
            'd': 'c'
        })

    def test_as_geslachtsaanduiding(self):
        valid = {
            'v': 'vrouw',
            'm': 'man',
            'o': 'onbekend',
        }
        for code, expected_result in valid.items():
            for aanduiding in [code.upper(), code.lower()]:
                self.assertEqual(MKSConverter.as_geslachtsaanduiding(aanduiding), expected_result)
        for a in ['x', 'X', '', 'anything', None]:
            self.assertIsNone(MKSConverter.as_geslachtsaanduiding(a))

        self.assertEqual('onbekend', MKSConverter.as_geslachtsaanduiding('something', no_value='waardeOnbekend'))
        self.assertEqual(None, MKSConverter.as_geslachtsaanduiding('something', no_value='nietGeautoriseerd'))

    def test_as_soort_verbintenis(self):
        valid = {
            'h': 'huwelijk',
            'p': 'geregistreerd_partnerschap'
        }
        for code, expected_result in valid.items():
            for aanduiding in [code.upper(), code.lower()]:
                self.assertEqual(MKSConverter.as_soort_verbintenis(aanduiding), expected_result)
        for a in ['x', 'X', '', 'anything', None]:
            self.assertEqual(MKSConverter.as_soort_verbintenis(a), None)

    def test_as_aanduiding_naamgebruik(self):
        valid = {
            'e': 'eigen',
            'n': 'eigen_partner',
            'p': 'partner',
            'v': 'partner_eigen',
        }
        for code, expected_result in valid.items():
            for aanduiding in [code.upper(), code.lower()]:
                self.assertEqual(MKSConverter.as_aanduiding_naamgebruik(aanduiding), expected_result)
        for aanduiding in ['x', 'X', '', 'anything', None]:
            self.assertIsNone(MKSConverter.as_aanduiding_naamgebruik(aanduiding))

    def test_as_aanduiding_bijzonder_nederlanderschap(self):
        valid = {
            'b': 'behandeld_als_nederlander',
            'v': 'vastgesteld_niet_nederlander',
        }
        for code, expected_result in valid.items():
            for aanduiding in [code.upper(), code.lower()]:
                self.assertEqual(MKSConverter.as_aanduiding_bijzonder_nederlanderschap(aanduiding), expected_result)
        for aanduiding in ['x', 'X', '', 'anything', None]:
            self.assertIsNone(MKSConverter.as_aanduiding_bijzonder_nederlanderschap(aanduiding))

    def test_true_if_exists(self):
        self.assertTrue(MKSConverter.true_if_exists('anything'))
        self.assertIsNone(MKSConverter.true_if_exists(None))

    def test_true_if_equals(self):
        values = [1, '1', True, False, '', None]
        false_values = [2, '2', False, True, None, '']
        for c, value in enumerate(values):
            true_if_equals = MKSConverter.true_if_equals(value)
            self.assertTrue(true_if_equals(value))
            
            self.assertFalse(true_if_equals(false_values[c]))

    def test_true_if_in(self):
        values = [1,2,3,4]
        true_if_in = MKSConverter.true_if_in(values)

        for value in [1,2,3,4]:
            self.assertTrue(true_if_in(value))

        # A value not in the list should return None
        self.assertIsNone(true_if_in(5))

        # A None value should return a None value
        self.assertIsNone(true_if_in(None))


    def test_get_communicatie(self):
        communicatie_parameters = {
            'persoon': {
                'geslachtsaanduiding': 'man',
                'naam': {
                    'aanduidingNaamgebruik': 'eigen',
                    'voorletters': 'M.',
                    'geslachtsnaam': 'Ruyter',
                    'voorvoegsel': 'de',
                }
            },
            'partners': [
                {
                    'naam': {
                        'geslachtsnaam': 'Engels',
                        'voorvoegsel': '',
                    },
                    'aangaanHuwelijkPartnerschap': {
                        'datum': '16360701'
                    },
                    'ontbindingHuwelijkPartnerschap': {
                        'datum': None
                    }
                },
                {
                    'naam': {
                        'geslachtsnaam': 'Velders',
                        'voorvoegsel': '',
                    },
                    'aangaanHuwelijkPartnerschap': {
                        'datum': '16310316'
                    },
                    'ontbindingHuwelijkPartnerschap': {
                        'datum': '16311231'
                    }
                },
            ]
        }
        communicatie = MKSConverter._get_communicatie(communicatie_parameters)
        self.assertEqual(communicatie.persoon.geslachtsnaam, 'Ruyter')
        self.assertEqual(communicatie.partner.geslachtsnaam, 'Engels')
        self.assertEqual(communicatie.partners[0].geslachtsnaam, 'Engels')
        self.assertEqual(communicatie.partnerhistorie[0].geslachtsnaam, 'Velders')

        self.assertEqual(MKSConverter.get_aanhef(communicatie_parameters), "Geachte heer De Ruyter")
        self.assertEqual(MKSConverter.get_aanschrijfwijze(communicatie_parameters), "M. de Ruyter")

    def test_get_nationaliteit(self):
        nationaliteit_parameters = {
            'aanduidingBijzonderNederlanderschap': None,
            'nationaliteiten': [
                {
                    'datumIngangGeldigheid': {
                        'datum': '2001-04-12',
                        'jaar': 2001,
                        'maand': 4,
                        'dag': 12
                    },
                    'datumVerlies': None,
                    'nationaliteit': {
                        'code': '0001',
                        'omschrijving': 'Nederlandse',
                    }
                },
                {
                    'datumIngangGeldigheid': {
                        'datum': '2001-04-12',
                        'jaar': 2001,
                        'maand': 4,
                        'dag': 12
                    },
                    'datumVerlies': "20020716",
                    'nationaliteit': {
                        'code': '0339',
                        'omschrijving': 'Turkse',
                    }
                }
            ]
        }
        nationaliteit = MKSConverter.get_nationaliteit(nationaliteit_parameters)

        # Expect one nationaliteit, Nederlandse
        self.assertEqual(len(nationaliteit), 1)
        self.assertEqual(nationaliteit[0]['nationaliteit']['omschrijving'], 'Nederlandse')

    def test_get_verblijf_buitenland(self):
        parameters = {
            'land': {
                'code': None
            }
        }
        self.assertIsNone(MKSConverter.get_verblijf_buitenland(parameters))

        parameters = {
            'land': {
                'code': '0000',
            }
        }
        self.assertEqual({
            'vertrokkenOnbekendWaarheen': True,
        }, MKSConverter.get_verblijf_buitenland(parameters))

        parameters = {
            'land': {
                'code': '1000',
                'omschrijving': 'Any Country',
            },
            'adresRegel1': '1',
            'adresRegel2': '2',
            'adresRegel3': '3',
        }
        self.assertEqual(parameters, MKSConverter.get_verblijf_buitenland(parameters))
