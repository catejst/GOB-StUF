"""
Request argument checks are defined here

"""
import re
import datetime


def validate_date(value: str):
    try:
        datetime.datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        return False

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
