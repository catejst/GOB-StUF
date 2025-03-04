"""
Request argument checks are defined here

"""
import re
import datetime

from gobstuf.reference_data.code_resolver import CodeResolver, DataItemNotFoundException
from gobstuf.stuf.message import WILDCARD_CHARS

MIN_WILDCARD_LENGTH = 2


def validate_date(value: str):
    try:
        datetime.datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        return False

    return True


def validate_gemeentecode(value: str):
    # Try to lookup a valid gemeente for the supplied value
    try:
        CodeResolver.get_gemeente(value)
    except DataItemNotFoundException:
        return False
    return True


def validate_wildcard_length(value: str):
    # Test if the value is a valid wildcard search when a wildcard is used, meaning it has at least 2 characters
    if any(wildcard in value for wildcard in WILDCARD_CHARS):
        wildcard_regex = ''.join(WILDCARD_CHARS)
        return len(re.sub(rf'[{wildcard_regex}]', '', value)) >= MIN_WILDCARD_LENGTH
    return True


def validate_wildcard_position(value: str):
    # Test if wildcards are at the beginning or end of the search string
    if any(wildcard in value for wildcard in WILDCARD_CHARS):
        wildcard_regex = ''.join(WILDCARD_CHARS)
        return re.match(rf'^[{wildcard_regex}]*[^{wildcard_regex}]+[{wildcard_regex}]*$', value)
    return True


class ArgumentCheck():

    is_boolean = {
        'check': lambda v: v in ['true', 'false'],
        'msg': {
            'code': 'boolean',
            'reason': 'Waarde is geen geldige boolean.'
        }
    }

    is_postcode = {
        'check': lambda v: re.match(r'^[1-9]{1}[0-9]{3}[A-Z]{2}$', v) is not None,
        'msg': {
            "code": "pattern",
            "reason": "Waarde voldoet niet aan patroon ^[1-9]{1}[0-9]{3}[A-Z]{2}$."
        }
    }

    is_integer = {
        'check': lambda v: re.match(r'^\d+$', v) is not None,
        'msg': {
            "code": "integer",
            "reason": "Waarde is geen geldige integer."
        }
    }

    is_alphabetic = {
        'check': lambda v: re.match(r'^[A-Za-z]+$', v) is not None,
        'msg': {
            "code": "alphabetic",
            "reason": "Waarde is geen geldige letter."
        }
    }

    is_positive_integer = {
        'check': lambda v: re.match(r'^[1-9][0-9]*$', v) is not None,
        'msg': {
            "code": "minimum",
            "reason": "Waarde is lager dan minimum 1."
        }
    }

    is_valid_date_format = {
        'check': lambda v: re.match(r'^\d{4}-\d{2}-\d{2}$', v) is not None,
        'msg': {
            "code": "invalidFormat",
            "reason": "Waarde voldoet niet aan het formaat YYYY-MM-DD",
        }
    }

    is_valid_date = {
        'check': validate_date,
        'msg': {
            "code": "invalidDate",
            "reason": "Waarde is geen geldige datum",
        }
    }

    is_valid_gemeentecode = {
        'check': validate_gemeentecode,
        'msg': {
            "code": "invalidGemeente",
            "reason": "Waarde is geen geldige gemeentecode.",
        }
    }

    has_min_wildcard_length = {
        'check': validate_wildcard_length,
        'msg': {
            "code": "invalidWildcardLength",
            "reason": "Zoeken met een wildcard vereist minimaal 2 karakters exclusief de wildcards.",
        }
    }

    is_valid_wildcard_position = {
        'check': validate_wildcard_position,
        'msg': {
            "code": "invalidWildcardPosition",
            "reason": "Een wildcard kan alleen aan het begin of eind van een zoekstring geplaatst worden.",
        }
    }

    @classmethod
    def has_max_length(cls, max):
        return {
            'check': lambda v: len(v) <= max,
            'msg': {
                "code": "maxLength",
                "reason": f"Waarde is langer dan maximale lengte {max}",
            }
        }

    @classmethod
    def has_min_length(cls, min):
        return {
            'check': lambda v: len(v) >= min,
            'msg': {
                "code": "minLength",
                "reason": f"Waarde is korter dan minimale lengte {min}",
            }
        }

    @classmethod
    def validate(cls, checks, value):
        """
        Validate the given value against one or more checks
        The first failing check is returned, or None if all checks pass

        :param checks:
        :param value:
        :return:
        """
        if not isinstance(checks, list):
            # Accept a single check as value by converting it to a list
            checks = [checks]
        for check in checks:
            if not check['check'](value):
                return check
