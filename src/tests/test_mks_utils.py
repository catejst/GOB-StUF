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
        self.assertFalse(MKSConverter._is_mks_datum("some string"))

    def test_yyyy(self):
        self.assertEqual(MKSConverter._yyyy("20200422"), "2020")
        self.assertEqual(MKSConverter._yyyy("202004221"), None)

    def test_mm(self):
        self.assertEqual(MKSConverter._mm("20200422"), "04")
        self.assertEqual(MKSConverter._mm("202004221"), None)

    def test_dd(self):
        self.assertEqual(MKSConverter._dd("20200422"), "22")
        self.assertEqual(MKSConverter._mm("202004221"), None)

    def test_as_datum(self):
        self.assertEqual(MKSConverter.as_datum("20200422"), "2020-04-22")
        self.assertEqual(MKSConverter.as_datum("202004221"), None)

    def test_as_jaar(self):
        self.assertEqual(MKSConverter.as_jaar("20200422"), 2020)
        self.assertEqual(MKSConverter.as_jaar("202004221"), None)

    def test_as_maand(self):
        self.assertEqual(MKSConverter.as_maand("20200422"), 4)
        self.assertEqual(MKSConverter.as_maand("202004221"), None)

    def test_as_dag(self):
        self.assertEqual(MKSConverter.as_dag("20200422"), 22)
        self.assertEqual(MKSConverter.as_dag("202004221"), None)

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

    def test_as_geslachtsaanduiding(self):
        for a in ['v', 'V']:
            self.assertEqual(MKSConverter.as_geslachtsaanduiding(a), 'vrouw')
        for a in ['m', 'M']:
            self.assertEqual(MKSConverter.as_geslachtsaanduiding(a), 'man')
        for a in ['o', 'O', 'x', 'X', '', 'anything', None]:
            self.assertEqual(MKSConverter.as_geslachtsaanduiding(a), 'onbekend')
