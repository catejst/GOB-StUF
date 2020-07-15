"""
Functionaliteit: Als gemeente wil ik de juiste en consistente briefaanhef in communicatie naar burgers
  Attribuut aanhef bij een ingeschreven persoon wordt gevuld door de provider
  om op deze wijze op eenduidige wijze een persoon te kunnen aanschrijven.
  De briefaanhef wordt gebruikt bovenaan een brief.

"""
import datetime

from typing import List
from functools import reduce
from operator import getitem

from gobstuf.indications import AanduidingNaamgebruik, Geslachtsaanduiding


def _get_value(dict, *args):
    """
    Get a dictionary value by path (a list of keys).

    Example:
        given a dict { 'a': { 'b': 'c' } }
        in order to access dict['a']['b'] without being sure that keys a en b exist
        you normally would program dict.get('a', {}).get('b')

        with this function you will have the same result using _get_value(dict, 'a', 'b')
    :param dict:
    :param *args: list of key values
    :return:
    """
    try:
        return reduce(getitem, args, dict)
    except (KeyError, TypeError):
        pass


def _datum_to_date(datum):
    """
    Convert a datum dictionary to a datetime.date object

    :param datum:
    :return:
    """
    try:
        return datetime.date(year=datum['jaar'], month=datum['maand'], day=datum['dag'])
    except (TypeError, KeyError):
        pass


class Persoon():

    def __init__(self, persoonsgegevens):
        """
        Attribuut aanhef wordt samengesteld op basis van:
        - voorvoegselGeslachtsnaam
        - geslachtsnaam
        - adellijkeTitel_predikaat
        - geslachtsaanduiding
        - aanduidingAanschrijving
        - voorvoegselGeslachtsnaam partner
        - geslachtsnaam partner
        - adellijkeTitel_predikaat partner
        - geslachtsaanduiding partner

        :param persoonsgegevens:
        """

        self.voorvoegsel_geslachtsnaam = _get_value(persoonsgegevens, 'naam', 'voorvoegsel') or ''
        self.voorletters = _get_value(persoonsgegevens, 'naam', 'voorletters') or ''
        self.geslachtsnaam = _get_value(persoonsgegevens, 'naam', 'geslachtsnaam') or ''
        self.adellijke_titel_predikaat = None
        self._geslachtsaanduiding = _get_value(persoonsgegevens, 'geslachtsaanduiding') or ''
        self._aanduiding_naamgebruik = _get_value(persoonsgegevens, 'naam', 'aanduidingNaamgebruik') or ''

    @property
    def geslachtsaanduiding(self):
        """
        Returns the Geslachtsaanduiding for this person
        :return:
        """
        return Geslachtsaanduiding().identifiers.get(self._geslachtsaanduiding)

    @property
    def aanduiding_naamgebruik(self):
        """
        Returns the AanduidingNaamgebruik for this person

        :return:
        """
        return AanduidingNaamgebruik().identifiers.get(self._aanduiding_naamgebruik)


class Partner(Persoon):

    def __init__(self, persoonsgegevens_partner):
        """
        A Partner is a Person with who a Person can relate,
        either by a huwelijk or a partnerschap

        A relation has a begin date and an optional end date

        :param persoonsgegevens_partner:
        """
        self._aangaan_huwelijk_partnerschap = persoonsgegevens_partner.get('aangaanHuwelijkPartnerschap')
        self._ontbinding_huwelijk_partnerschap = persoonsgegevens_partner.get('ontbindingHuwelijkPartnerschap')
        # Partner is a persoon
        super().__init__(persoonsgegevens_partner)

    @property
    def aangaan_huwelijk_partnerschap_date(self):
        """
        Returns the start date for the relation

        :return:
        """
        if self._aangaan_huwelijk_partnerschap:
            return _datum_to_date(self._aangaan_huwelijk_partnerschap.get('datum'))

    @property
    def ontbinding_huwelijk_partnerschap_date(self):
        """
        Returns the end date for the relation

        :return:
        """
        if self._ontbinding_huwelijk_partnerschap and\
                self._ontbinding_huwelijk_partnerschap.get('indicatieHuwelijkPartnerschapBeeindigd', True):
            return _datum_to_date(self._ontbinding_huwelijk_partnerschap.get('datum'))


class Communicatie():

    def __init__(self, persoon: Persoon, partners: List[Partner] = None, partnerhistorie: List[Partner] = None):
        """
        Communicatie with a persoon requires an aanhef and aanschrijfwijze

        These properties depend upon the Persoon and its (former) partners

        :param persoon:
        :param partners:
        :param partnerhistorie:
        """
        self.persoon = persoon
        self.partners = partners or []
        self.partnerhistorie = partnerhistorie or []

        # Determine the partner for this Persoon that is used for the aanhef en aanschrijfwijze
        self.partner = self._get_partner()

    def _naamgebruik(self, capitalize_eerste_voorvoegsel):
        """

        :param capitalize_eerste_voorvoegsel:
        :return:
        """

        # Composition aanhef
        # GA VV1 GN1 [- VV2 GN2]
        # De waarde van aanduidingNaamgebruik bepaalt hoe de aanhef wordt samengesteld
        # uit de naam van de persoon en de naam van de partner.
        if not self.persoon.aanduiding_naamgebruik:
            # Required attribute is missing
            raise AttributeError

        vv1, gn1, vv2, gn2 = {
            AanduidingNaamgebruik.EIGEN: self._eigen_naam,
            AanduidingNaamgebruik.EIGEN_PARTNER: self._eigen_partner_naam,
            AanduidingNaamgebruik.PARTNER: self._partner_naam,
            AanduidingNaamgebruik.PARTNER_EIGEN: self._partner_eigen_naam
        }[self.persoon.aanduiding_naamgebruik]()

        if capitalize_eerste_voorvoegsel:
            vv1 = vv1.capitalize()

        naamgebruik = self._voorvoegsel_geslachtsnaam(vv1, gn1)
        if vv2 or gn2:
            naamgebruik += f"-{self._voorvoegsel_geslachtsnaam(vv2, gn2)}"
        return naamgebruik

    def _eigen_naam(self):
        vv = self.persoon.voorvoegsel_geslachtsnaam
        gn = self.persoon.geslachtsnaam
        return vv, gn, None, None

    def _eigen_partner_naam(self):
        vv1, gn1, _, _ = self._eigen_naam()
        vv2, gn2, _, _ = self._partner_naam()
        return vv1, gn1, vv2, gn2

    def _partner_naam(self):
        vv = self.partner.voorvoegsel_geslachtsnaam
        gn = self.partner.geslachtsnaam
        return vv, gn, None, None

    def _partner_eigen_naam(self):
        vv1, gn1, _, _ = self._partner_naam()
        vv2, gn2, _, _ = self._eigen_naam()
        return vv1, gn1, vv2, gn2

    @property
    def aanhef(self):
        """
        Attribuut aanhef bij een ingeschreven persoon wordt gevuld door de provider
        om op deze wijze op eenduidige wijze een persoon te kunnen aanschrijven.

        Het voorvoegsel van de eerste geslachtsnaam in de briefaanhef
        wordt met een hoofdletter geschreven.

        :return:
        """
        try:
            return f"{self._geachte()} {self._naamgebruik(capitalize_eerste_voorvoegsel=True)}"
        except AttributeError:
            # A required attribute is missing, eg partner name with naamgebruik != eigen
            pass

    @property
    def aanschrijfwijze(self):
        """
        De briefaanhef wordt gebruikt bovenaan een brief.

        :return:
        """
        try:
            return f"{self.persoon.voorletters} {self._naamgebruik(capitalize_eerste_voorvoegsel=False)}"
        except AttributeError:
            # A required attribute is missing, eg partner name with naamgebruik != eigen
            pass

    def _get_partner(self):
        """
        Returns the partner of this Persoon to be used in the determination of aanhef en aanschrijfwijze

        :return:
        """
        # Als er meerdere actuele (niet ontbonden) huwelijken/partnerschappen zijn
        # En de aanschijfwijze is ongelijk aan 'Eigen'
        # Dan wordt als partnernaam de naam van de eerste partner (oudste relatie) gebruikt.
        partners = [p for p in self.partners
                    if p.aangaan_huwelijk_partnerschap_date and not p.ontbinding_huwelijk_partnerschap_date]
        if partners:
            return min(partners, key=lambda p: p.aangaan_huwelijk_partnerschap_date)

        # Als er meerdere ontbonden huwelijken/partnerschappen zijn
        # En er geen actueel (niet ontbonden) huwelijk/partnerschap is
        # En de aanschijfwijze is ongelijk aan 'Eigen'
        # Dan wordt als partnernaam de naam van de laatst ontbonden relatie gebruikt.
        partners = [p for p in self.partnerhistorie if p.ontbinding_huwelijk_partnerschap_date]
        if partners:
            return max(partners, key=lambda p: p.ontbinding_huwelijk_partnerschap_date)

        if self.partners:
            # Last resort, return the first partner if the person has partners
            return self.partners[0]

    def _geachte(self):
        # "Geachte mevrouw", "Geachte heer",
        # "Hooggeboren heer", "Hooggeboren vrouwe",
        # "Hoogwelgeboren heer", "Hoogwelgeboren vrouwe",
        # "Hoogheid"
        if self.persoon.adellijke_titel_predikaat or\
                (self.partner and self.partner.adellijke_titel_predikaat):
            # Wanneer de persoon een adellijke titel of predikaat heeft, wordt de aanhef volgens de volgende tabel:
            # adellijke_titel_predikaat_aanhef = {
            #     'Baron': 'Hoogwelgeboren heer',
            #     'Barones': 'Hoogwelgeboren vrouwe',
            #     'Graaf': 'Hooggeboren heer',
            #     'Gravin': 'Hooggeboren vrouwe',
            #     'Hertog': 'Hoogwelgeboren heer',
            #     'Hertogin': 'Hoogwelgeboren vrouwe',
            #     'Jonkheer': 'Hoogwelgeboren heer',
            #     'Jonkvrouw': 'Hoogwelgeboren vrouwe',
            #     'Markies': 'Hoogwelgeboren heer',
            #     'Markiezin': 'Hoogwelgeboren vrouwe',
            #     'Prins': 'Hoogheid',
            #     'Prinses': 'Hoogheid',
            #     'Ridder': 'Hoogwelgeboren heer'
            # }
            raise NotImplementedError("Adelijke titels have not been implemented")
        else:
            # Voor een persoon zonder adellijke titel of predicaat begint de briefaanhef met
            # “Geachte mevrouw” of “Geachte heer”, afhankelijk van het geslacht van de persoon
            return {
                Geslachtsaanduiding.MAN: 'Geachte heer',
                Geslachtsaanduiding.VROUW: 'Geachte mevrouw',
                Geslachtsaanduiding.ONBEKEND: 'Geachte'
            }[self.persoon.geslachtsaanduiding] if self.persoon.geslachtsaanduiding else None

    def _voorvoegsel_geslachtsnaam(self, voorvoegsel, geslachtsnaam):
        """
        Combine an optional voorvoegsel and the geslachtsnaam

        Example: "van der", "Velzen" => "van der Velzen"
                 None, "Velzen" => "Velzen"
        :param voorvoegsel:
        :param geslachtsnaam:
        :return:
        """
        return f"{voorvoegsel + ' ' if voorvoegsel else ''}{geslachtsnaam}"
