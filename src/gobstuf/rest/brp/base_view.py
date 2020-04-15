from flask.views import MethodView
from flask import request, abort, Response
from flask_hal.document import Document
from requests.exceptions import HTTPError
from abc import abstractmethod

from gobstuf.certrequest import cert_post
from gobstuf.stuf.brp.base_request import StufRequest
from gobstuf.stuf.exception import NoStufAnswerException
from gobstuf.stuf.brp.error_response import StufErrorResponse
from gobstuf.config import ROUTE_SCHEME, ROUTE_NETLOC, ROUTE_PATH


MKS_USER_HEADER = 'MKS_GEBRUIKER'
MKS_APPLICATION_HEADER = 'MKS_APPLICATIE'


def headers_required_decorator(headers):
    def headers_required(f):
        def decorator(*args, **kwargs):
            if not all([request.headers.get(h) for h in headers]):
                return abort(Response(response='Missing required MKS headers', status=400))

            return f(*args, **kwargs)
        return decorator
    return headers_required


class StufRestView(MethodView):
    """StufRestView.

    Maps a GET request with URL parameters defined in kwargs to an MKS StUF request.

    Should be extended with a request_template and response_template.
    """
    decorators = [headers_required_decorator([MKS_USER_HEADER, MKS_APPLICATION_HEADER])]

    def get(self, **kwargs):
        """kwargs contains the URL parameters, for example {'bsn': xxxx'} when the requested resource is
        /brp/ingeschrevenpersonen/<bsn>

        :param kwargs: Dictionary with URL parameters
        :return:
        """

        # Request MKS with given request_template
        request_template = self.request_template(
            request.headers.get(MKS_USER_HEADER),
            request.headers.get(MKS_APPLICATION_HEADER),
            kwargs
        )
        response = self._make_request(request_template)

        try:
            response.raise_for_status()
        except HTTPError:
            # Received error status code from MKS (always 500)
            response_obj = StufErrorResponse(response.text)
            return self._error_response(response_obj)

        # Map MKS response back to REST response.
        response_obj = self.response_template(response.text)

        try:
            return self._json_response(response_obj.get_mapped_object())
        except NoStufAnswerException:
            # Return 404, answer section is empty
            return self._not_found_response(**kwargs)

    def _make_request(self, request_template: StufRequest):
        """Makes the MKS request

        :param request_template:
        :return:
        """
        soap_headers = {
            'Soapaction': request_template.soap_action,
            'Content-Type': 'text/xml'
        }
        url = f'{ROUTE_SCHEME}://{ROUTE_NETLOC}{ROUTE_PATH}'

        return cert_post(url, data=request_template.to_string(), headers=soap_headers)

    def _json_response(self, data: dict, status_code: int = 200):
        """Builds an HAL JSON formatted Flask response object.

        :param data:
        :param status_code:
        :return:
        """
        doc = Document(data=data)
        return Response(response=doc.to_json(), content_type='application/hal+json'), status_code

    def _error_response(self, response_obj: StufErrorResponse):
        """Builds the error response based on the error response received from MKS

        :param response_obj:
        :return:
        """
        code = response_obj.get_error_code()

        if code == 'Fo02':
            # Invalid MKS APPLICATIE/GEBRUIKER. Raise 403
            data = {
                'status': 403,
                'title': 'MKS authorisatie mislukt',
            }
            return self._json_response(data, 403)

        # Other unknown code
        return self._json_response({
            'mks_code': response_obj.get_error_code(),
            'mks_error': response_obj.get_error_string(),
        }, 400)

    def _not_found_response(self, **kwargs):
        data = {
            'title': 'Opgevraagde resource bestaat niet',
            'status': 404,
            'detail': self.get_not_found_message(**kwargs),
            'instance': request.url,
            'code': 'notFound',
        }

        return self._json_response(data, 404)

    @property
    @abstractmethod
    def request_template(self):
        """The StufRequestTemplate used to query MKS

        :return:
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def response_template(self):
        """The StufResponse returned from MKS.

        :return:
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_not_found_message(self, **kwargs):
        """Should return a 'not found' message.

        :param kwargs: the URL parameters for this request
        :return:
        """
        pass  # pragma: no cover
