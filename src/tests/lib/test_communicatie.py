from unittest import TestCase

import datetime

from gobstuf.mks_utils import AanduidingNaamgebruik, Geslachtsaanduiding
from gobstuf.lib.communicatie import Communicatie, Persoon, Partner, _get_value, _datum_to_date

class TestCommunicatie(TestCase):

    def test_single(self):
        in_het_veld = {
            'geslachtsaanduiding': 'man',
            'naam': {
                'aanduidingNaamgebruik': 'eigen',
                'voorletters': 'H.',
                'geslachtsnaam': 'Veld',
                'voorvoegsel': 'in het',
            }
        }
        self.assertEqual(Communicatie(in_het_veld).aanhef, "Geachte heer In het Veld")
        self.assertEqual(Communicatie(in_het_veld).aanschrijfwijze, "H. in het Veld")

        in_het_veld['geslachtsaanduiding'] = 'vrouw'
        self.assertEqual(Communicatie(in_het_veld).aanhef, "Geachte mevrouw In het Veld")
        self.assertEqual(Communicatie(in_het_veld).aanschrijfwijze, "H. in het Veld")

        in_het_veld['geslachtsaanduiding'] = 'onbekend'
        self.assertEqual(Communicatie(in_het_veld).aanhef, "Geachte In het Veld")
        self.assertEqual(Communicatie(in_het_veld).aanschrijfwijze, "H. in het Veld")

    def test_geen_adellijke_titel_of_predikaat(self):
        in_het_veld = {
            'geslachtsaanduiding': None,
            'naam': {
                'aanduidingNaamgebruik': None,
                'voorletters': 'H.',
                'geslachtsnaam': 'Veld',
                'voorvoegsel': 'in het',
            }
        }
        groenen = {
            'geslachtsaanduiding': None,
            'naam': {
                'aanduidingNaamgebruik': None,
                'voorletters': 'F.',
                'geslachtsnaam': 'Groenen',
            }
        }
        van_velzen = {
            'geslachtsaanduiding': None,
            'naam': {
                'aanduidingNaamgebruik': None,
                'voorletters': 'I.',
                'geslachtsnaam': 'Velzen',
                'voorvoegsel': 'van',
            }
        }
        groenink = {
            'geslachtsaanduiding': None,
            'naam': {
                'aanduidingNaamgebruik': None,
                'voorletters': 'F',
                'geslachtsnaam': 'Groenink'
            }
        }

        #   | aanduidingNaamgebruik | geslachtsaanduiding |samenstelling aanhef | aanschrijfwijze           | aanhef                                 |
        #   | Eigen                 | Man                 | GA VV GN            | H. in het Veld            | Geachte heer In het Veld               |
        in_het_veld['geslachtsaanduiding'] = 'man'
        in_het_veld['naam']['aanduidingNaamgebruik'] = 'eigen'
        self.assertEqual(Communicatie(in_het_veld, van_velzen).aanhef, "Geachte heer In het Veld")
        self.assertEqual(Communicatie(in_het_veld, van_velzen).aanschrijfwijze, "H. in het Veld")

        #   | aanduidingNaamgebruik | geslachtsaanduiding |samenstelling aanhef | aanschrijfwijze           | aanhef                                 |
        #   | Eigen                 | Man                 | GA VV GN            | F. Groenen                | Geachte heer Groenen                   |
        groenen['geslachtsaanduiding'] = 'man'
        groenen['naam']['aanduidingNaamgebruik'] = 'eigen'
        self.assertEqual(Communicatie(groenen, groenink).aanhef, "Geachte heer Groenen")
        self.assertEqual(Communicatie(groenen, groenink).aanschrijfwijze, "F. Groenen")

        #   | aanduidingNaamgebruik | geslachtsaanduiding |samenstelling aanhef | aanschrijfwijze           | aanhef                                 |
        #   | Partner na eigen      | Vrouw               | GA VV GN-VP GP      | I. van Velzen-in het Veld | Geachte mevrouw Van Velzen-in het Veld |
        van_velzen['geslachtsaanduiding'] = 'vrouw'
        van_velzen['naam']['aanduidingNaamgebruik'] = 'eigen_partner'
        self.assertEqual(Communicatie(van_velzen, in_het_veld).aanhef, "Geachte mevrouw Van Velzen-in het Veld")
        self.assertEqual(Communicatie(van_velzen, in_het_veld).aanschrijfwijze, "I. van Velzen-in het Veld")

        #   | aanduidingNaamgebruik | geslachtsaanduiding |samenstelling aanhef | aanschrijfwijze           | aanhef                                 |
        #   | Partner na eigen      | Vrouw               | GA VV GN-VP GP      | F. Groenen-Groenink       | Geachte mevrouw Groenen-Groenink       |
        groenen['geslachtsaanduiding'] = 'vrouw'
        groenen['naam']['aanduidingNaamgebruik'] = 'eigen_partner'
        self.assertEqual(Communicatie(groenen, groenink).aanhef, "Geachte mevrouw Groenen-Groenink")
        self.assertEqual(Communicatie(groenen, groenink).aanschrijfwijze, "F. Groenen-Groenink")

        #   | aanduidingNaamgebruik | geslachtsaanduiding |samenstelling aanhef | aanschrijfwijze           | aanhef                                 |
        #   | Partner               | Vrouw               | GA VP GP            | S. van Velzen             | Geachte mevrouw Van Velzen             |
        in_het_veld['geslachtsaanduiding'] = 'vrouw'
        in_het_veld['naam']['aanduidingNaamgebruik'] = 'partner'
        in_het_veld['naam']['voorletters'] = 'S.'
        self.assertEqual(Communicatie(in_het_veld, van_velzen).aanhef, "Geachte mevrouw Van Velzen")
        self.assertEqual(Communicatie(in_het_veld, van_velzen).aanschrijfwijze, "S. van Velzen")

        #   | aanduidingNaamgebruik | geslachtsaanduiding |samenstelling aanhef | aanschrijfwijze           | aanhef                                 |
        #   | Partner               | Vrouw               | GA VP GP            | J.F.R. Groenen            | Geachte mevrouw Groenen                |
        groenink['geslachtsaanduiding'] = 'vrouw'
        groenink['naam']['aanduidingNaamgebruik'] = 'partner'
        groenink['naam']['voorletters'] = 'J.F.R.'
        self.assertEqual(Communicatie(groenink, groenen).aanhef, "Geachte mevrouw Groenen")
        self.assertEqual(Communicatie(groenink, groenen).aanschrijfwijze, "J.F.R. Groenen")

        #   | aanduidingNaamgebruik | geslachtsaanduiding |samenstelling aanhef | aanschrijfwijze           | aanhef                                 |
        #   | Partner voor eigen    | Man                 | GA VP GP-VV GN      | F. in het Veld-van Velzen | Geachte heer In het Veld-van Velzen    |
        van_velzen['geslachtsaanduiding'] = 'man'
        van_velzen['naam']['aanduidingNaamgebruik'] = 'partner_eigen'
        van_velzen['naam']['voorletters'] = 'F.'
        self.assertEqual(Communicatie(van_velzen, in_het_veld).aanhef, "Geachte heer In het Veld-van Velzen")
        self.assertEqual(Communicatie(van_velzen, in_het_veld).aanschrijfwijze, "F. in het Veld-van Velzen")

        #   | aanduidingNaamgebruik | geslachtsaanduiding |samenstelling aanhef | aanschrijfwijze           | aanhef                                 |
        #   | Partner voor eigen    | Man                 | GA VP GP-VV GN      | F. Groenen-Groenink       | Geachte heer Groenen-Groenink          |
        groenink['geslachtsaanduiding'] = 'man'
        groenink['naam']['aanduidingNaamgebruik'] = 'partner_eigen'
        groenink['naam']['voorletters'] = 'F.'
        self.assertEqual(Communicatie(groenink, groenen).aanhef, "Geachte heer Groenen-Groenink")
        self.assertEqual(Communicatie(groenink, groenen).aanschrijfwijze, "F. Groenen-Groenink")

    def test_voorvoegsels_met_hoofdletter_of_kleine_letter(self):
        in_het_veld = {
            'geslachtsaanduiding': None,
            'naam': {
                'aanduidingNaamgebruik': None,
                'geslachtsnaam': 'Veld',
                'voorvoegsel': 'In het',
            }
        }
        van_velzen = {
            'geslachtsaanduiding': None,
            'naam': {
                'aanduidingNaamgebruik': None,
                'geslachtsnaam': 'Velzen',
                'voorvoegsel': 'van',
            }
        }

        # | aanduidingAanschrijving | geslachtsaanduiding | VV     | GN     | VP     | GP     | aanhef                                 |
        # | E                       | man                 | In het | Veld   | van    | Velzen | Geachte heer In het Veld               |
        in_het_veld['geslachtsaanduiding'] = 'man'
        in_het_veld['naam']['aanduidingNaamgebruik'] = 'eigen'
        self.assertEqual(Communicatie(in_het_veld, van_velzen).aanhef, "Geachte heer In het Veld")

        # | aanduidingAanschrijving | geslachtsaanduiding | VV     | GN     | VP     | GP     | aanhef                                 |
        # | N                       | vrouw               | van    | Velzen | In het | Veld   | Geachte mevrouw Van Velzen-In het Veld |
        van_velzen['geslachtsaanduiding'] = 'vrouw'
        van_velzen['naam']['aanduidingNaamgebruik'] = 'eigen_partner'
        self.assertEqual(Communicatie(van_velzen, in_het_veld).aanhef, "Geachte mevrouw Van Velzen-In het Veld")

        # | aanduidingAanschrijving | geslachtsaanduiding | VV     | GN     | VP     | GP     | aanhef                                 |
        # | P                       | vrouw               | In het | Veld   | van    | Velzen | Geachte mevrouw Van Velzen             |
        in_het_veld['geslachtsaanduiding'] = 'vrouw'
        in_het_veld['naam']['aanduidingNaamgebruik'] = 'partner'
        self.assertEqual(Communicatie(in_het_veld, van_velzen).aanhef, "Geachte mevrouw Van Velzen")

        # | aanduidingAanschrijving | geslachtsaanduiding | VV     | GN     | VP     | GP     | aanhef                                 |
        # | V                       | man                 | van    | Velzen | In het | Veld   | Geachte heer In het Veld-van Velzen    |
        van_velzen['geslachtsaanduiding'] = 'man'
        van_velzen['naam']['aanduidingNaamgebruik'] = 'partner_eigen'
        self.assertEqual(Communicatie(van_velzen, in_het_veld).aanhef, "Geachte heer In het Veld-van Velzen")

    def test_meerdere_actuele_relaties(self):
        # Gegeven de ingeschreven persoon de heer F.C. Groen is getrouwd in 1958 met Geel
        # En de ingeschreven persoon is getrouwd in 1961 met Roodt
        # En geen van beide relaties is beëindigd
        # En de ingeschreven persoon heeft aanduidingAanschrijving='V'
        # Als de ingeschreven persoon wordt geraadpleegd
        # Dan is in het antwoord naam.aanhef=Geachte heer Geel-Groen
        groenen = {
            'geslachtsaanduiding': 'man',
            'naam': {
                'aanduidingNaamgebruik': 'partner_eigen',
                'geslachtsnaam': 'Groen',
            }
        }
        geel = {
            'geslachtsaanduiding': 'vrouw',
            'naam': {
                'geslachtsnaam': 'Geel',
            },
            "aangaanHuwelijkPartnerschap": {
                "datum": {
                    "datum": "1958-01-01",
                    "jaar": 1958,
                    "maand": 1,
                    "dag": 1
                }
            },
        }
        roodt = {
            'geslachtsaanduiding': 'vrouw',
            'naam': {
                'geslachtsnaam': 'Roodt',
            },
            "aangaanHuwelijkPartnerschap": {
                "datum": {
                    "datum": "1961-01-01",
                    "jaar": 1961,
                    "maand": 1,
                    "dag": 1
                }
            },
        }
        self.assertEqual(Communicatie(groenen, [geel, roodt]).aanhef, "Geachte heer Geel-Groen")
        self.assertEqual(Communicatie(groenen, [roodt, geel]).aanhef, "Geachte heer Geel-Groen")

    def test_meerdere_ontbonden_relaties(self):
        # Gegeven de ingeschreven persoon de heer J. Wit is getrouwd in 1958 met Geel
        # En de ingeschreven persoon is getrouwd in 1961 met Roodt
        # En het huwelijk met Geel is ontbonden in 1960
        # En het huwelijk met Roodt is ontbonden in 2006
        # En de ingeschreven persoon heeft aanduidingAanschrijving='V'
        # Als de ingeschreven persoon wordt geraadpleegd
        # Dan is in het antwoord naam.aanhef=Geachte heer Roodt-Wit

        # Gegeven de ingeschreven persoon de heer J. Wit is getrouwd in 1958 met Zwart
        # En de ingeschreven persoon is getrouwd in 1961 met Blaauw
        # En het huwelijk met Blaauw is ontbonden in 1983
        # En het huwelijk met Zwart is ontbonden in 2006
        # En de ingeschreven persoon heeft aanduidingAanschrijving='V'
        # Als de ingeschreven persoon wordt geraadpleegd
        # Dan is in het antwoord naam.aanhef=Geachte heer Zwart-Wit
        wit = {
            'geslachtsaanduiding': 'man',
            'naam': {
                'aanduidingNaamgebruik': 'partner_eigen',
                'geslachtsnaam': 'Wit',
            }
        }
        zwart = {
            'geslachtsaanduiding': 'vrouw',
            'naam': {
                'geslachtsnaam': 'Zwart',
            },
            "aangaanHuwelijkPartnerschap": {
                "datum": {
                    "datum": "1958-01-01",
                    "jaar": 1958,
                    "maand": 1,
                    "dag": 1
                }
            },
            "ontbindingHuwelijkPartnerschap": {
                "indicatieHuwelijkPartnerschapBeeindigd": True,
                "datum": {
                    "datum": "2006-01-01",
                    "jaar": 2006,
                    "maand": 1,
                    "dag": 1
                }
            }
        }
        blaauw = {
            'geslachtsaanduiding': 'vrouw',
            'naam': {
                'geslachtsnaam': 'Blaauw',
            },
            "aangaanHuwelijkPartnerschap": {
                "datum": {
                    "datum": "1961-01-01",
                    "jaar": 1961,
                    "maand": 1,
                    "dag": 1
                }
            },
            "ontbindingHuwelijkPartnerschap": {
                "indicatieHuwelijkPartnerschapBeeindigd": True,
                "datum": {
                    "datum": "1983-01-01",
                    "jaar": 1983,
                    "maand": 1,
                    "dag": 1
                }
            }
        }
        self.assertEqual(Communicatie(wit, None, [zwart, blaauw]).aanhef, "Geachte heer Zwart-Wit")
        self.assertEqual(Communicatie(wit, None, [blaauw, zwart]).aanhef, "Geachte heer Zwart-Wit")

    def test_adellijke_titel_predikaat(self):
        persoonsgegevens = {}
        communicatie = Communicatie(persoonsgegevens)
        communicatie.persoon.adellijke_titel_predikaat = 'een adelijke titel'
        with self.assertRaises(NotImplementedError):
            communicatie._geachte()


class TestPersoon(TestCase):

    def test_persoon(self):
        in_het_veld = {
            'geslachtsaanduiding': 'man',
            'naam': {
                'aanduidingNaamgebruik': 'eigen',
                'voorletters': 'H.',
                'geslachtsnaam': 'Veld',
                'voorvoegsel': 'in het',
            }
        }
        persoon = Persoon(in_het_veld)
        self.assertEqual(persoon.geslachtsaanduiding, Geslachtsaanduiding.MAN)
        self.assertEqual(persoon.aanduiding_naamgebruik, AanduidingNaamgebruik.EIGEN)

class TestPartner(TestCase):

    def test_partner(self):
        blaauw = {
            'geslachtsaanduiding': 'vrouw',
            'naam': {
                'geslachtsnaam': 'Blaauw',
            },
            "aangaanHuwelijkPartnerschap": {
                "datum": {
                    "datum": "1961-01-01",
                    "jaar": 1961,
                    "maand": 1,
                    "dag": 1
                }
            },
            "ontbindingHuwelijkPartnerschap": {
                "indicatieHuwelijkPartnerschapBeeindigd": True,
                "datum": {
                    "datum": "1983-01-01",
                    "jaar": 1983,
                    "maand": 1,
                    "dag": 1
                }
            }
        }
        partner = Partner(blaauw)
        self.assertEqual(partner.aangaan_huwelijk_partnerschap_date, datetime.date(year=1961, month=1, day=1))
        self.assertEqual(partner.ontbinding_huwelijk_partnerschap_date, datetime.date(year=1983, month=1, day=1))

        blaauw['ontbindingHuwelijkPartnerschap']['indicatieHuwelijkPartnerschapBeeindigd'] = False
        self.assertEqual(partner.ontbinding_huwelijk_partnerschap_date, None)

        blaauw['aangaanHuwelijkPartnerschap']['datum']['dag'] = None
        self.assertEqual(partner.aangaan_huwelijk_partnerschap_date, None)

class TestUtils(TestCase):

    def test_get_value(self):
        dict = {
            'a': {
                'b': {
                    'c': 'd'
                }
            }
        }
        self.assertEqual(_get_value(dict, 'a', 'b', 'c'), 'd')
        self.assertEqual(_get_value(dict, 'a', 'b', 'c', 'd'), None)

    def test_datum_to_date(self):
        self.assertEqual(_datum_to_date(None), None)

        datum = {
            "jaar": 1,
            "maand": 2,
            "dag": 3
        }
        self.assertEqual(_datum_to_date(datum), datetime.date(year=1, month=2, day=3))

        # datum to date returns None an an incomplete date
        for attr in ['jaar', 'maand', 'dag']:
            old_value = datum[attr]
            datum[attr] = None
            self.assertEqual(_datum_to_date(datum), None)
            datum[attr] = old_value
            self.assertEqual(_datum_to_date(datum), datetime.date(year=1, month=2, day=3))
