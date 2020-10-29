import traceback
import logging

from flask.views import MethodView
from flask import g, request, abort, Response
from requests.exceptions import HTTPError
from abc import abstractmethod

from gobstuf.certrequest import cert_post
from gobstuf.auth.routes import MKS_USER_KEY, MKS_APPLICATION_KEY
from gobstuf.stuf.brp.base_request import StufRequest
from gobstuf.stuf.brp.base_response import StufMappedResponse
from gobstuf.stuf.exception import NoStufAnswerException
from gobstuf.stuf.brp.error_response import StufErrorResponse
from gobstuf.rest.brp.rest_response import RESTResponse
from gobstuf.config import ROUTE_SCHEME, ROUTE_NETLOC, ROUTE_PATH_310, CORRELATION_ID_HEADER
from gobstuf.rest.brp.argument_checks import ArgumentCheck


def authentication_required_decorator(keys):
    """Decorator used in StufRestView to check that MKS authentication is set

    :param headers:
    :return:
    """
    def keys_required(f):
        def decorator(*args, **kwargs):
            if not all([g.get(key) for key in keys]):
                return abort(Response(response='Missing required MKS authentication', status=400))

            return f(*args, **kwargs)
        return decorator
    return keys_required


class StufRestView(MethodView):
    """StufRestView.

    Maps a GET request with URL parameters defined in kwargs to an MKS StUF request.

    Should be extended with a request_template and response_template.
    """

    # Decorator makes sure MKS authentication is set
    decorators = [authentication_required_decorator([MKS_USER_KEY, MKS_APPLICATION_KEY])]

    # Passed to the response template. Values are the default values.
    functional_query_parameters = {
        'expand': None,
    }

    # The options for the expand parameter, for example 'partners', 'ouders', ...
    expand_options = []

    WILDCARD_CHECKS = [ArgumentCheck.has_min_wildcard_length, ArgumentCheck.is_valid_wildcard_position]

    def get(self, **kwargs):
        try:
            errors = self._validate(**kwargs)
        except StufRestFilterView.InvalidQueryParametersException as e:
            errors = e.err

        assert getattr(self, '_validate_called', False), \
            f"Make sure to call super()._validate() from children of {self.__class__}"

        if errors:
            return RESTResponse.bad_request(**errors)

        try:
            return self._get(**kwargs)
        except Exception:
            logging.error(f"ERROR: Request failed:")
            logging.error(traceback.format_exc())
            return RESTResponse.internal_server_error()

    def _validate_request_args(self, **kwargs):
        """
        Validate the request arguments and path variables

        :param args:
        :return:
        """
        args = {**self._request_template_parameters(**kwargs)}

        # Add other request args (such as functional query parameters)
        args.update({k: v for k, v in request.args.items() if k not in args})

        invalid_params = []
        for arg, value in args.items():
            invalid_param = self._validate_request_arg(arg, value)
            if invalid_param:
                invalid_params.append(invalid_param)

        if invalid_params:
            param_names = ', '.join([param['name'] for param in invalid_params])
            return {
                "invalid-params": invalid_params,
                "title": "Een of meerdere parameters zijn niet correct.",
                "detail": f"De foutieve parameter(s) zijn: {param_names}.",
                "code": "paramsValidation"
            }

    def _validate_request_arg(self, arg, value):
        """
        Validate a request argument

        This is a default implementation. Any subclass can override this method
        and perform a custom check on any or all request arguments

        :param arg:
        :param value:
        :return:
        """
        checks = self.request_template.parameter_checks.get(arg)

        # If the argument is allowed to have a wildcard, check if the wildcard search is valid
        if arg in self.request_template.parameter_wildcards:
            if checks:
                checks.extend(self.WILDCARD_CHECKS)
            else:
                checks = self.WILDCARD_CHECKS

        if not checks:
            return
        error = ArgumentCheck.validate(checks, value)
        if error:
            return {
                'name': arg,
                **error['msg'],
            }

    def _request_template_parameters(self, **kwargs):
        """Return kwargs by default. Childs may override this

        :param kwargs:
        :return:
        """
        return kwargs

    def _validate(self, **kwargs) -> dict:
        """Validates this request. Called before anything else in handling the request.

        Returns the dictionary with errors, or an empty dictionary when no errors occurred.

        :param kwargs:
        :return:
        """
        # Control variable to make sure this method is called from child classes
        self._validate_called = True

        # Start with validation of query parameters and path variables
        invalid_params = self._validate_request_args(**kwargs)
        if invalid_params:
            return invalid_params

        # Validate functional query parameters (expand)
        functional_params = self._get_functional_query_parameters()

        """
        Test validity of expand parameter.
        If expand is set, expand should only contain values as defined in expand_options.
        Expand can be a comma-separated list of options.
        """
        if functional_params['expand'] is not None and not (
                isinstance(functional_params['expand'], str) and
                all([expand in self.expand_options for expand in functional_params['expand'].split(',')])
        ):
            return {
                'invalid-params': 'expand',
                'title': 'De waarde van expand wordt niet geaccepteerd',
                'detail': f'De mogelijke waarden zijn: {",".join(self.expand_options)}'
            }

        return {}

    def _get_functional_query_parameters(self):
        return {k: self._transform_query_parameter_value(request.args.get(k, v))
                for k, v in self.functional_query_parameters.items()}

    def _get_wildcard_query_parameters(self):
        wildcards = {wildcard: request.args.get(wildcard) for wildcard in self.request_template.parameter_wildcards
                     if wildcard in request.args}
        return {'wildcards': wildcards}

    def _get(self, **kwargs):
        """kwargs contains the URL parameters, for example {'bsn': xxxx'} when the requested resource is
        /brp/ingeschrevenpersonen/<bsn>

        :param kwargs: Dictionary with URL parameters
        :return:
        """

        # Request MKS with given request_template
        request_template = self.request_template(
            g.get(MKS_USER_KEY),
            g.get(MKS_APPLICATION_KEY),
            correlation_id=request.headers.get(CORRELATION_ID_HEADER)
        )
        request_template.set_values(self._request_template_parameters(**kwargs))

        response = self._make_request(request_template)

        try:
            response.raise_for_status()
        except HTTPError:
            # Received error status code from MKS (always 500)
            response_obj = StufErrorResponse(response.text)
            return self._error_response(response_obj)

        # Map MKS response back to REST response. Include the path parameters to the response
        response_obj = self.response_template(response.text,
                                              **self._get_functional_query_parameters(),
                                              **self._get_wildcard_query_parameters(),
                                              **kwargs)

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
        url = f'{ROUTE_SCHEME}://{ROUTE_NETLOC}{ROUTE_PATH_310}'

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
        logging.error(f"MKS error {response_obj.get_error_code()}. Code {response_obj.get_error_string()}")

        return RESTResponse.bad_request()

    def _transform_query_parameter_value(self, value: str):
        """Transforms the string value of the query parameter to the corresponding python type for booleans and null
        values.

        :param value:
        :return:
        """
        if not isinstance(value, str):
            return value
        elif value == '':
            return None

        lower = value.lower()

        if lower in ('null', 'none'):
            return None
        elif lower in ('true',):
            return True
        elif lower in ('false',):
            return False
        else:
            return value

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

    optional_query_parameters = []

    def _request_template_parameters(self, **kwargs):
        """Returns the url path variables and query parameters as request template parameters

        Raises an InvalidQueryParametersException. Caller should have called _validate() first.

        :param kwargs:
        :return:
        """
        return {**kwargs, **self._get_query_parameters()}

    def _validate(self, **kwargs):
        """Validates that a correct combination of query parameters is provided.

        :param kwargs:
        :return:
        """
        errors = super()._validate(**kwargs)
        if errors:
            return errors

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
            If no match is found an InvalidQueryParametersException is raised

        :return:
        """
        for combination in self.query_parameter_combinations:
            args = {arg: self._transform_query_parameter_value(request.args.get(arg)) for arg in combination}
            if all(args.values()):
                # Get all optional query parameters with their values
                optional_args = {k: v for k, v in {
                    arg: self._transform_query_parameter_value(request.args.get(arg))
                    for arg in self.optional_query_parameters
                }.items() if v}

                return {
                    **args,
                    **optional_args,
                }

        detail = "Combinatie van gevulde velden was niet correct. " +\
                 "Geef waarde aan één van de volgende veld combinaties: " + \
                 " of ".join([" en ".join(c) for c in self.query_parameter_combinations])
        raise self.InvalidQueryParametersException({
            'title': "Minimale combinatie van parameters moet worden opgegeven.",
            'detail': detail,
            'code': "paramsCombination"
        })

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

        def __init__(self, err=None):
            self.err = err
            super().__init__()
