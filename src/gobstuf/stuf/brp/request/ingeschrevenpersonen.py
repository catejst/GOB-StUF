from abc import ABC

from gobstuf.stuf.brp.base_request import StufRequest


class IngeschrevenpersonenStufRequest(StufRequest, ABC):
    BSN_LENGTH = 9

    template = 'ingeschrevenpersonen.xml'
    content_root_elm = 'soapenv:Body BG:npsLv01'
    soap_action = 'http://www.egem.nl/StUF/sector/bg/0310/npsLv01Integraal'

    def validate_bsn(self, bsn):
        """
        The BSN should have the correct length, if not return an params error

        :param args:
        :return:
        """
        if len(bsn) != self.BSN_LENGTH:
            name = "burgerservicenummer"
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
    }

    def validate(self, args):
        """
        Validate the request arguments

        The BSN should have the correct length, if not return an params error

        :param args:
        :return:
        """
        if args.get('burgerservicenummer'):
            bsn_error = self.validate_bsn(args['burgerservicenummer'])
            if bsn_error:
                return bsn_error

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
        bsn_error = self.validate_bsn(args['bsn'])
        if bsn_error:
            return bsn_error

        return super().validate(args)
