from unittest import TestCase
from unittest.mock import patch

import datetime

from gobstuf.mks_utils import MKSConverter, _today

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

    @patch('gobstuf.mks_utils.CodeResolver')
    def test_get_gemeente_omschrijving(self, mock_code_resolver):
        mock_code_resolver.get_gemeente.return_value = 'any omschrijving'
        self.assertEqual(MKSConverter.get_gemeente_omschrijving("any gemeente"), 'any omschrijving')

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
        birthday = "19830500"
        mock_today.return_value = datetime.date(2019, 5, 31)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), None)
        mock_today.return_value = datetime.date(2019, 6, 1)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), 36)
        mock_today.return_value = datetime.date(2019, 4, 30)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), 35)

        # Alleen jaar van geboorte datum is bekend
        birthday = "19830000"
        mock_today.return_value = datetime.date(2019, 5, 31)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), None)

        # Persoon is overleden
        birthday = "19830526"
        mock_today.return_value = datetime.date(2019, 5, 26)
        self.assertEqual(MKSConverter.as_leeftijd(birthday, is_overleden=True), None)

        # Volledig onbekend geboortedatum
        self.assertEqual(MKSConverter.as_leeftijd(None), None)

        # Geboren op 29 februari in een schrikkeljaar
        birthday = "19960229"
        mock_today.return_value = datetime.date(2016, 2, 29)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), 20)
        mock_today.return_value = datetime.date(2017, 2, 28)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), 20)
        mock_today.return_value = datetime.date(2017, 3, 1)
        self.assertEqual(MKSConverter.as_leeftijd(birthday), 21)

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
            self.assertEqual(MKSConverter.as_geslachtsaanduiding(a), 'onbekend')

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
