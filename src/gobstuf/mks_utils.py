"""
MKS utility methods

"""

import datetime
from dateutil.relativedelta import relativedelta


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
        try:
            datetime.datetime.strptime(mks_datum, cls._MKS_DATUM_PARSE_FORMAT)
        except (ValueError, TypeError):
            return False
        return len(mks_datum) == len(cls._MKS_DATUM_FORMAT)

    @classmethod
    def _yyyy(cls, mks_datum):
        return mks_datum[0:4] if cls._is_mks_datum(mks_datum) else None

    @classmethod
    def _mm(cls, mks_datum):
        return mks_datum[4:6] if cls._is_mks_datum(mks_datum) else None

    @classmethod
    def _dd(cls, mks_datum):
        return mks_datum[6:8]

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
    def as_leeftijd(cls, mks_geboortedatum):
        if cls._is_mks_datum(mks_geboortedatum):
            # Interpret all dates as dates in the current timezone
            now = _today()
            birthday = datetime.datetime.strptime(mks_geboortedatum, cls._MKS_DATUM_PARSE_FORMAT)
            return relativedelta(now, birthday).years

    @classmethod
    def as_geslachtsaanduiding(cls, mks_geslachtsaanduiding):
        mks_geslachtsaanduiding = mks_geslachtsaanduiding or ""
        return {
            'v': 'vrouw',
            'm': 'man'
        }.get(mks_geslachtsaanduiding.lower(), 'onbekend')
