from gobstuf.rest.brp.rest_response import RESTResponse
from gobstuf.stuf.brp.base_response import StufResponse


class UnknownErrorCode(Exception):
    pass


class StufErrorResponse(StufResponse):
    code_path = 'soapenv:Envelope soapenv:Body soapenv:Fault detail'

    def _get_error_details(self):
        """Returns detail element

        :return:
        """
        return list(self.stuf_message.find_elm(self.code_path))[0]

    def get_berichtcode(self):
        return self.stuf_message.get_elm_value('StUF:stuurgegevens StUF:berichtcode', self._get_error_details())

    def get_error_omschrijving(self):
        return self.stuf_message.get_elm_value('StUF:body StUF:omschrijving', self._get_error_details())

    def get_error_plek(self):
        return self.stuf_message.get_elm_value('StUF:body StUF:plek', self._get_error_details())

    def get_error_code(self):
        return self.stuf_message.get_elm_value('StUF:body StUF:code', self._get_error_details())

    def get_http_response(self):
        """Returns HTTP response object for given MKS code.

        :return:
        """
        if self.get_berichtcode() != 'Fo02':
            raise UnknownErrorCode()

        responses = {
            # De stuurgegevens zijn onjuist gevuld
            'StUF001': RESTResponse.bad_request(),
            # Het interactieve proces voor het afhandelen van een synchrone vraag is niet actief
            'StUF002': RESTResponse.internal_server_error(),
            # De gevraagde gegevens zijn niet beschikbaar
            'StUF003': RESTResponse.not_found(),
            # De gevraagde sortering wordt niet ondersteund
            'StUF004': RESTResponse.internal_server_error(),
            # Er heeft zich in de StUF-communicatie een time-out voorgedaan
            'StUF005': RESTResponse.internal_server_error(),
            # Het vraagbericht bevat als selectiecriterium zowel de sleutel in het vragende systeem als het ontvangende
            # systeem,
            'StUF006': RESTResponse.internal_server_error(),
            # Het ontvangende systeem ondersteunt niet het bevraagd worden op sleutel in het vragende systeem
            'StUF007': RESTResponse.internal_server_error(),
            # De beantwoording van het vraagbericht vergt meer systeemresources dan het antwoordende systeem
            # beschikbaar heeft
            'StUF008': RESTResponse.internal_server_error(),
            # Het vraagbericht is gericht aan een niet bekend systeem
            'StUF009': RESTResponse.internal_server_error(),
            # Het vragende systeem is niet geautoriseerd voor de gevraagde gegevens
            'StUF010': RESTResponse.forbidden(),
            # De syntax van het StUF-vraagbericht is onjuist
            'StUF011': RESTResponse.internal_server_error(),
            # Het ontvangende systeem ondersteunt niet de afhandeling van asynchrone vraagberichten
            'StUF012': RESTResponse.internal_server_error(),
            # Het vragende systeem is bij het ontvangende systeem niet bekend
            'StUF013': RESTResponse.internal_server_error(),
        }

        try:
            return responses[self.get_error_code()]
        except KeyError:
            raise UnknownErrorCode()
