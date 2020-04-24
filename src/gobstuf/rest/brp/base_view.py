from flask.views import MethodView
from flask import request, abort, Response
from requests.exceptions import HTTPError
from abc import abstractmethod

from gobstuf.certrequest import cert_post
from gobstuf.stuf.brp.base_request import StufRequest
from gobstuf.stuf.exception import NoStufAnswerException
from gobstuf.stuf.brp.error_response import StufErrorResponse
from gobstuf.rest.brp.rest_response import RESTResponse
from gobstuf.config import ROUTE_SCHEME, ROUTE_NETLOC, ROUTE_PATH


MKS_USER_HEADER = 'MKS_GEBRUIKER'
MKS_APPLICATION_HEADER = 'MKS_APPLICATIE'


def headers_required_decorator(headers):
    """Decorator used in StufRestView to check that MKS headers are set

    :param headers:
    :return:
    """
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

    # Decorator makes sure the MKS headers are set
    decorators = [headers_required_decorator([MKS_USER_HEADER, MKS_APPLICATION_HEADER])]

    def get(self, **kwargs):
        try:
            return self._get(**kwargs)
        except Exception as e:
            print(f"ERROR: Request failed: {str(e)}")
            return RESTResponse.internal_server_error()

    def _get(self, **kwargs):
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
        errors = request_template.validate(kwargs)
        if errors:
            return RESTResponse.bad_request(**errors)

        response = self._make_request(request_template)

        # print("RESPONSE", response.text)

        try:
            response.raise_for_status()
        except HTTPError:
            # Received error status code from MKS (always 500)
            response_obj = StufErrorResponse(response.text)
            return self._error_response(response_obj)

        # Map MKS response back to REST response.
        response_obj = self.response_template(response.text)

        try:
            data = response_obj.get_answer_object()
        except NoStufAnswerException:
            # Return 404, answer section is empty
            return RESTResponse.not_found(detail=self.get_not_found_message(**kwargs))
        else:
            return RESTResponse.ok(data)

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

        # print("REQUEST", request_template.to_string())

        return cert_post(url, data=request_template.to_string(), headers=soap_headers)

    def _error_response(self, response_obj: StufErrorResponse):
        """Builds the error response based on the error response received from MKS

        :param response_obj:
        :return:
        """
        code = response_obj.get_error_code()

        if code == 'Fo02':
            # Invalid MKS APPLICATIE/GEBRUIKER. Raise 403
            return RESTResponse.forbidden()

        # Other unknown code
        print(f"MKS error {response_obj.get_error_code()}. Code {response_obj.get_error_string()}")

        return RESTResponse.bad_request()

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
