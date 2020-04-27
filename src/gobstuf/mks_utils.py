"""
MKS utility methods

"""
import datetime
from abc import ABC, abstractmethod

from gobstuf.reference_data.code_resolver import CodeResolver


def _today():
    return datetime.datetime.now().date()


class Indication(ABC):

    def __init__(self, id):
        """
        Register the id in uppercase
        Resolve the id to get the corresponding description
        :param id:
        """
        self.id = (id or "").upper()
        self._description = self.indications.get(self.id)

    @property
    @abstractmethod
    def indications(self):
        pass  # pragma: no cover

    @property
    def description(self):
        return self._description


class Geslachtsaanduiding(Indication):
    VROUW = 'V'
    MAN = 'M'
    ONBEKEND = 'O'

    @property
    def indications(self):
        return {
            self.VROUW: 'vrouw',
            self.MAN: 'man',
            self.ONBEKEND: 'onbekend'
        }


class AanduidingNaamgebruik(Indication):
    EIGEN = 'E'
    EIGEN_PARTNER = 'N'
    PARTNER = 'P'
    PARTNER_EIGEN = 'V'

    @property
    def indications(self):
        return {
            self.EIGEN: 'eigen',
            self.EIGEN_PARTNER: 'eigen_partner',
            self.PARTNER: 'partner',
            self.PARTNER_EIGEN: 'partner_eigen'
        }


class IncompleteDateIndicator(Indication):
    JAAR_MAAND_EN_DAG_ONBEKEND = 'J2'
    MAAND_EN_DAG_ONBEKEND = 'M'
    DAG_ONBEKEND = 'D'
    DATUM_IS_VOLLEDIG = 'V'

    @property
    def indications(self):
        return {
            self.JAAR_MAAND_EN_DAG_ONBEKEND: 'Jaar, maand en dag onbekend',
            self.MAAND_EN_DAG_ONBEKEND: 'Maand en dag onbekend',
            self.DAG_ONBEKEND: 'Dag onbekend',
            self.DATUM_IS_VOLLEDIG: 'Datum is volledig'
        }

    def is_jaar_bekend(self):
        return self.id not in [self.JAAR_MAAND_EN_DAG_ONBEKEND]

    def is_maand_bekend(self):
        return self.id not in [self.JAAR_MAAND_EN_DAG_ONBEKEND, self.MAAND_EN_DAG_ONBEKEND]

    def is_dag_bekend(self):
        return self.id not in [self.JAAR_MAAND_EN_DAG_ONBEKEND, self.MAAND_EN_DAG_ONBEKEND, self.DAG_ONBEKEND]

    def is_datum_volledig(self):
        return all([self.is_jaar_bekend(), self.is_maand_bekend(), self.is_dag_bekend()])


class MKSConverter:
    """
    Utility class to convert MKS values to return in the REST response

    Input values are in StUF MKS format
    Output values are in REST API output format
    """
    _MKS_DATUM_FORMAT = "yyyymmdd"
    _MKS_DATUM_PARSE_FORMAT = "%Y%m%d"

    @classmethod
    def _is_mks_datum(cls, mks_datum):
        if not mks_datum or len(mks_datum) != len(cls._MKS_DATUM_FORMAT):
            # Minimal requirement is that the length is OK
            return False

        try:
            # Simply try to parse the date, if that succeeds then return True
            datetime.datetime.strptime(mks_datum, cls._MKS_DATUM_PARSE_FORMAT)
            return True
        except (ValueError, TypeError):
            return False

    @classmethod
    def _yyyy(cls, mks_datum):
        return mks_datum[0:4] if cls._is_mks_datum(mks_datum) else None

    @classmethod
    def _mm(cls, mks_datum):
        return mks_datum[4:6] if cls._is_mks_datum(mks_datum) else None

    @classmethod
    def _dd(cls, mks_datum):
        return mks_datum[6:8] if cls._is_mks_datum(mks_datum) else None

    @classmethod
    def as_datum_broken_down(cls, mks_datum, ind_onvolledige_datum=None):
        if cls._is_mks_datum(mks_datum):
            return {
                'datum': cls.as_datum(mks_datum, ind_onvolledige_datum),
                'jaar': cls.as_jaar(mks_datum, ind_onvolledige_datum),
                'maand': cls.as_maand(mks_datum, ind_onvolledige_datum),
                'dag': cls.as_dag(mks_datum, ind_onvolledige_datum)
            }

    @classmethod
    def as_datum(cls, mks_datum, ind_onvolledige_datum=None):
        if cls._is_mks_datum(mks_datum) and IncompleteDateIndicator(ind_onvolledige_datum).is_datum_volledig():
            return f"{cls._yyyy(mks_datum)}-{cls._mm(mks_datum)}-{cls._dd(mks_datum)}"

    @classmethod
    def as_jaar(cls, mks_datum, ind_onvolledige_datum=None):
        if cls._is_mks_datum(mks_datum) and IncompleteDateIndicator(ind_onvolledige_datum).is_jaar_bekend():
            return int(cls._yyyy(mks_datum))

    @classmethod
    def as_maand(cls, mks_datum, ind_onvolledige_datum=None):
        if cls._is_mks_datum(mks_datum) and IncompleteDateIndicator(ind_onvolledige_datum).is_maand_bekend():
            return int(cls._mm(mks_datum))

    @classmethod
    def as_dag(cls, mks_datum, ind_onvolledige_datum=None):
        if cls._is_mks_datum(mks_datum) and IncompleteDateIndicator(ind_onvolledige_datum).is_dag_bekend():
            return int(cls._dd(mks_datum))

    @classmethod
    def _get_age(cls, now, birthday):
        """
        Age calculation that takes leap years into account

        :param now:
        :param birthday:
        :return:
        """
        try:
            day = birthday.replace(year=now.year)
        except ValueError:
            # Fails in leap year, set day to first of next month
            day = birthday.replace(year=now.year, month=birthday.month + 1, day=1)

        if day > now:
            return now.year - birthday.year - 1
        else:
            return now.year - birthday.year

    @classmethod
    def as_leeftijd(cls, mks_geboortedatum,  ind_onvolledige_datum=None, overlijdensdatum=None):
        """
        birthday string as age

        Accepts birthday strings with unknown month. The age is unknown in the same month
        but otherwise simple known as if the birthday was on a arbitrary day in the month

        :param mks_geboortedatum:
        :param is_overleden:
        :return:
        """
        if not mks_geboortedatum or overlijdensdatum:
            return None

        incomplete_date_indicator = IncompleteDateIndicator(ind_onvolledige_datum)
        if not (incomplete_date_indicator.is_jaar_bekend() and incomplete_date_indicator.is_maand_bekend()):
            return None

        if cls._is_mks_datum(mks_geboortedatum):
            # Interpret all dates as dates in the current timezone
            now = _today()
            birthday = datetime.datetime.strptime(mks_geboortedatum, cls._MKS_DATUM_PARSE_FORMAT).date()
            day_is_unknown = not incomplete_date_indicator.is_dag_bekend()
            if not (day_is_unknown and now.month == birthday.month):
                return cls._get_age(now=now, birthday=birthday)

    @classmethod
    def as_geslachtsaanduiding(cls, mks_geslachtsaanduiding):
        return Geslachtsaanduiding(mks_geslachtsaanduiding).description or \
               Geslachtsaanduiding(Geslachtsaanduiding.ONBEKEND).description

    @classmethod
    def as_aanduiding_naamgebruik(cls, mks_aanduiding_naamgebruik):
        return AanduidingNaamgebruik(mks_aanduiding_naamgebruik).description

    @classmethod
    def as_code(cls, length):
        """
        Returns a function to convert a code to a zero padded string of length <length>
        :param length:
        :return:
        """
        def as_code(mks_code):
            return mks_code.zfill(length)
        return as_code

    @classmethod
    def get_gemeente_omschrijving(cls, mks_code):
        return CodeResolver.get_gemeente(mks_code)

    @classmethod
    def get_land_omschrijving(cls, mks_code):
        return CodeResolver.get_land(mks_code)
