from flask.views import MethodView
from flask import request, abort, Response
from requests.exceptions import HTTPError
from abc import abstractmethod

from gobstuf.certrequest import cert_post
from gobstuf.stuf.brp.base_request import StufRequest
from gobstuf.stuf.brp.base_response import StufMappedResponse
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

    # The key/value pairs in this dictionary will be set as properties on the response template object
    response_template_properties = {}

    def get(self, **kwargs):
        errors = self._validate(**kwargs)

        if errors:
            return RESTResponse.bad_request(**errors)

        try:
            return self._get(**kwargs)
        except Exception as e:
            print(f"ERROR: Request failed: {str(e)}")
            return RESTResponse.internal_server_error()

    def _request_template_parameters(self, **kwargs):
        """Return kwargs by default. Childs may override this

        :param kwargs:
        :return:
        """
        return kwargs

    def _validate(self, **kwargs) -> dict:
        """Validates this request. Called before anything else in handling the request.

        Returns the dictionary with errors, or an empty dictionary when no errors occurred.
        Default behaviour is no validation.

        :param kwargs:
        :return:
        """
        return {}

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
            self._request_template_parameters(**kwargs)
        )
        errors = request_template.validate(kwargs)
        if errors:
            return RESTResponse.bad_request(**errors)

        response = self._make_request(request_template)

        try:
            response.raise_for_status()
        except HTTPError:
            # Received error status code from MKS (always 500)
            response_obj = StufErrorResponse(response.text)
            return self._error_response(response_obj)

        # Map MKS response back to REST response.
        response_obj = self.response_template(response.text, **self.response_template_properties)

        return self._build_response(response_obj, **kwargs)

    def _build_response(self, response_obj: StufMappedResponse, **kwargs):
        """Return single object response by default

        Overridden by StufRestFilterView to create a list of objects

        :param response_obj:
        :param kwargs:
        :return:
        """
        try:
            data = response_obj.get_answer_object()
        except NoStufAnswerException:
            # Return 404, answer section is empty
            return RESTResponse.not_found(detail=self.get_not_found_message(**kwargs))
        else:
            return RESTResponse.ok(data, response_obj.get_links(data))

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


class StufRestFilterView(StufRestView):
    """StufRestFilterView

    A StufRestView that returns a list of objects instead of a single object.
    Filtering/searching is done with query parameters

    """

    # Define the possible combinations of query parameters in a request. By default the combination of 'no parameters'
    # is allowed only. First matching combination is returned.
    query_parameter_combinations = [
        (),
    ]

    def _request_template_parameters(self, **kwargs):
        """Returns the url path variables and query parameters as request template parameters

        Raises an InvalidQueryParametersException. Should call _validate() first.

        :param kwargs:
        :return:
        """
        return {**kwargs, **self._get_query_parameters()}

    def _validate(self, **kwargs):
        """Validates that a correct combination of query parameters is provided.

        :param kwargs:
        :return:
        """
        try:
            self._request_template_parameters(**kwargs)
            return {}
        except self.InvalidQueryParametersException:
            return self._query_parameters_error()

    def _query_parameters_error(self) -> dict:
        """Returns the error that is returned to the user when the combination of query parameters is not
        according to specification.

        Provides the possible valid parameter combinations in the error message.

        :return:
        """
        combinations = ' , '.join([combination
                                   for combination in [
                                       ' / '.join(parameters)
                                       if parameters
                                       else 'no params'
                                       for parameters in self.query_parameter_combinations]
                                   ])
        return {
            "title": "De opgegeven combinatie van parameters is niet correct",
            "detail": f"De mogelijke combinaties zijn: {combinations}",
            "code": "paramsRequired",
        }

    def _build_response(self, response_obj: StufMappedResponse, **kwargs):
        """Returns the REST response, of the format:

        _embedded: {
            ingeschrevenpersonen: [
                { response object 1},
                { response object 2},
                { ... },
            ]
        }

        :param response_obj:
        :param kwargs:
        :return:
        """
        data = response_obj.get_all_answer_objects()
        return RESTResponse.ok({
            '_embedded': {
                self.name: data,
            }
        }, {})

    def _get_query_parameters(self) -> dict:
        """Returns the query parameters as k:v pairs. Returns only the parameters that are in the first matching
        combination in query_parameter_combinations.

        Example:
            query_parameter_combinations = [('a', 'b'), ('a', 'c', 'd'), ()]

            If a, b, c and d are all present and set in the query string, only a and b will be returned, because these
            form the first match.
            If b would be missing, a, c and d would be returned.
            If a were missing an empty dict would be returned. No query parameters is an option in this case, because
            of the empty tuple.
            If no match is found an InnvalidQueryParametersException is raised

        :return:
        """
        for combination in self.query_parameter_combinations:
            args = {arg: request.args.get(arg) for arg in combination}
            if all(args.values()):
                return args

        raise self.InvalidQueryParametersException()

    def get_not_found_message(self, **kwargs):  # pragma: no cover
        raise NotImplementedError('Method should never be called')

    @property
    def name(self):  # pragma: no cover
        """Return the name of the root element of this collection of objects:

        _embedded: {
            self.name: []
        }

        :return:
        """
        raise NotImplementedError('Implement this method in the child')

    class InvalidQueryParametersException(Exception):
        pass
