import datetime
import re

from abc import ABC

from gobstuf.stuf.brp.base_request import StufRequest

# Defined at the module level so it's only compiled once
date_match = re.compile(r'^\d{4}-\d{2}-\d{2}$')


class IngeschrevenpersonenStufRequest(StufRequest, ABC):
    BSN_LENGTH = 9

    template = 'ingeschrevenpersonen.xml'
    content_root_elm = 'soapenv:Body BG:npsLv01'
    soap_action = 'http://www.egem.nl/StUF/sector/bg/0310/npsLv01Integraal'

    def validate_bsn(self, bsn, name):
        """
        The BSN should have the correct length, if not return an params error

        :param args:
        :return:
        """
        if len(bsn) != self.BSN_LENGTH:
            if len(bsn) < self.BSN_LENGTH:
                invalid_param = {
                    "code": "minLength",
                    "reason": f"Waarde is korter dan minimale lengte {self.BSN_LENGTH}."
                }
            else:
                invalid_param = {
                    "code": "maxLength",
                    "reason": f"Waarde is langer dan maximale lengte {self.BSN_LENGTH}."
                }
            invalid_param['name'] = name
            return self.params_errors([name], [invalid_param])


class IngeschrevenpersonenFilterStufRequest(IngeschrevenpersonenStufRequest):
    parameter_paths = {
        'burgerservicenummer': 'BG:gelijk BG:inp.bsn',
        'verblijfplaats__postcode': 'BG:gelijk BG:verblijfsadres BG:aoa.postcode',
        'verblijfplaats__huisnummer': 'BG:gelijk BG:verblijfsadres BG:aoa.huisnummer',
        'geboorte__datum': 'BG:gelijk BG:geboortedatum',
        'naam__geslachtsnaam': 'BG:gelijk BG:geslachtsnaam',
    }

    def convert_param_geboorte__datum(self, value: str):
        """Transforms the YYYY-MM-DD value to YYYYMMDD

        :param value:
        :return:
        """
        assert date_match.match(value), "This value should already be validated here"

        return value.replace('-', '')

    def validate_date(self, date_str: str, name: str):
        """Validates a date string:
        - Should have the format YYYY-MM-DD
        - Should be valid date

        :param date_str:
        :return:
        """

        if not date_match.match(date_str):
            # This case would also throw a ValueError in the strptime call below, but it's added here to provide a
            # better error message.
            return self.params_errors([name], [{
                "code": "invalidFormat",
                "reason": "Waarde voldoet niet aan het formaat YYYY-MM-DD",
                "name": name,
            }])

        try:
            datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return self.params_errors([name], [{
                "code": "invalidDate",
                "reason": "Ongeldige datum opgegeven",
                "name": name,
            }])

    def validate_geslachtsnaam(self, value: str, name: str):
        MAX_LENGTH = 200

        if len(value) > MAX_LENGTH:
            return self.params_errors([name], [{
                "code": "maxLength",
                "reason": f"Waarde is langer dan maximale lengte {MAX_LENGTH}",
                "name": name,
            }])

    def validate(self, args):
        """
        Validate the request arguments

        The BSN should have the correct length, if not return an params error

        :param args:
        :return:
        """

        validations = [
            ('burgerservicenummer', self.validate_bsn),
            ('geboorte__datum', self.validate_date),
            ('naam__geslachtsnaam', self.validate_geslachtsnaam),
        ]

        # Call the validate methods for each argument. Only if the argument exists.
        for argument_name, validate_func in validations:
            if args.get(argument_name):
                error = validate_func(args[argument_name], argument_name)
                if error:
                    return error

        return super().validate(args)


class IngeschrevenpersonenBsnStufRequest(IngeschrevenpersonenStufRequest):
    BSN_LENGTH = 9

    parameter_paths = {
        'bsn': 'BG:gelijk BG:inp.bsn'
    }

    def validate(self, args):
        """
        Validate the request arguments

        The BSN should have the correct length, if not return an params error

        :param args:
        :return:
        """
        bsn_error = self.validate_bsn(args['bsn'], 'burgerservicenummer')
        if bsn_error:
            return bsn_error

        return super().validate(args)
