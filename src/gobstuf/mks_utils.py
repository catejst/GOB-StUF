"""
MKS utility methods

"""
import re
import datetime

from gobstuf.reference_data.code_resolver import CodeResolver


def _today():
    return datetime.datetime.now().date()


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
    def as_datum_broken_down(cls, mks_datum):
        if cls._is_mks_datum(mks_datum):
            return {
                'datum': cls.as_datum(mks_datum),
                'jaar': cls.as_jaar(mks_datum),
                'maand': cls.as_maand(mks_datum),
                'dag': cls.as_dag(mks_datum)
            }

    @classmethod
    def as_datum(cls, mks_datum):
        if cls._is_mks_datum(mks_datum):
            return f"{cls._yyyy(mks_datum)}-{cls._mm(mks_datum)}-{cls._dd(mks_datum)}"

    @classmethod
    def as_jaar(cls, mks_datum):
        if cls._is_mks_datum(mks_datum):
            return int(cls._yyyy(mks_datum))

    @classmethod
    def as_maand(cls, mks_datum):
        if cls._is_mks_datum(mks_datum):
            return int(cls._mm(mks_datum))

    @classmethod
    def as_dag(cls, mks_datum):
        if cls._is_mks_datum(mks_datum):
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
    def as_leeftijd(cls, mks_geboortedatum, is_overleden=False):
        """
        birthday string as age

        Accepts birthday strings with unknown month. The age is unknown in the same month
        but otherwise simple known as if the birthday was on a arbitrary day in the month

        :param mks_geboortedatum:
        :param is_overleden:
        :return:
        """
        if not mks_geboortedatum or is_overleden:
            return None

        unknown_day_pattern = r'(.*)(00)$'
        day_is_unknown = re.match(unknown_day_pattern, mks_geboortedatum)
        if day_is_unknown:
            mks_geboortedatum = re.sub(unknown_day_pattern, r'\g<1>15', mks_geboortedatum)

        if cls._is_mks_datum(mks_geboortedatum):
            # Interpret all dates as dates in the current timezone
            now = _today()
            birthday = datetime.datetime.strptime(mks_geboortedatum, cls._MKS_DATUM_PARSE_FORMAT).date()
            if not (day_is_unknown and now.month == birthday.month):
                return cls._get_age(now=now, birthday=birthday)

    @classmethod
    def as_geslachtsaanduiding(cls, mks_geslachtsaanduiding):
        mks_geslachtsaanduiding = mks_geslachtsaanduiding or ""
        return {
            'v': 'vrouw',
            'm': 'man'
        }.get(mks_geslachtsaanduiding.lower(), 'onbekend')

    @classmethod
    def as_aanduiding_naamgebruik(cls, mks_aanduiding_naamgebruik):
        mks_aanduiding_naamgebruik = mks_aanduiding_naamgebruik or ""
        return {
            'e': 'eigen',
            'n': 'eigen_partner',
            'p': 'partner',
            'v': 'partner_eigen'
        }.get(mks_aanduiding_naamgebruik.lower())

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
