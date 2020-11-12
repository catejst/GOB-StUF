from unittest import TestCase
from unittest.mock import patch, MagicMock

from gobstuf.auth.routes import MKS_USER_KEY, MKS_APPLICATION_KEY
from gobstuf.rest.brp.base_view import (
    StufRestView, HTTPError,
    NoStufAnswerException,
    StufRestFilterView
)


class TestStufRestView(TestCase):


    def test_validate_inheritance(self):
        """StufRestView sets a control parameter when _validate is called, so it won't happen that a child class
        forgets to call its parent's validate() method.

        :return:
        """
        class StufRestViewNaughtyChild(StufRestView):

            def _validate(self, **kwargs) -> dict:
                return {}

            @property
            def request_template(self):
                return ""

            @property
            def response_template(self):
                return ""

            def get_not_found_message(self, **kwargs):
                return ""

        class StufRestViewObedientChild(StufRestView):

            def _validate(self, **kwargs) -> dict:
                return super()._validate(**kwargs)

            def _get(self, **kwargs):
                return 'OK'

            def _get_functional_query_parameters(self):
                return {'expand': None}

            @property
            def request_template(self):
               return ""

            @property
            def response_template(self):
                return ""

            def get_not_found_message(self, **kwargs):
                return ""

        # Naughty child does not call super()._validate() and raises an error
        naughty_child = StufRestViewNaughtyChild()
        naughty_child._validate_request_args = MagicMock(return_value=None)

        kwargs = {'kw': 'arg'}
        with self.assertRaises(AssertionError):
            naughty_child.get(**kwargs)

        # Obedient child does call super()._validate() and succeeds
        obedient_child = StufRestViewObedientChild()
        obedient_child._validate_request_args = MagicMock(return_value=None)

        self.assertEqual('OK', obedient_child.get(**kwargs))

    @patch("gobstuf.rest.brp.base_view.ROUTE_SCHEME", 'scheme')
    @patch("gobstuf.rest.brp.base_view.ROUTE_NETLOC", 'netloc')
    @patch("gobstuf.rest.brp.base_view.ROUTE_PATH_310", '/route/path')
    @patch("gobstuf.rest.brp.base_view.cert_post")
    def test_make_request(self, mock_post):
        stufreq = MagicMock()
        stufreq.soap_action = 'THE SOAP action'
        stufreq.to_string = lambda: 'string repr'

        view = StufRestView()
        self.assertEqual(mock_post.return_value, view._make_request(stufreq))

        mock_post.assert_called_with(
            'scheme://netloc/route/path',
            data='string repr',
            headers={
                'Soapaction': 'THE SOAP action',
                'Content-Type': 'text/xml',
            }
        )

    @patch("gobstuf.rest.brp.base_view.request")
    @patch("gobstuf.rest.brp.base_view.RESTResponse")
    def test_error_response(self, mock_rest_response, mock_request):
        mock_request.url = 'REQUEST_URL'
        view = StufRestView()
        response_arg = MagicMock()

        self.assertEqual(mock_rest_response.bad_request.return_value,
                         view._error_response(response_arg))

        # Generic error
        mock_rest_response.bad_request.assert_called_with()

        # Fo02 MKS error
        response_arg.get_error_code.return_value = 'Fo02'
        view._error_response(response_arg)

        mock_rest_response.forbidden.assert_called_with()

    @patch("gobstuf.rest.brp.base_view.request")
    def test_validate(self, mock_request):
        view = StufRestView()
        view._validate_request_args = MagicMock(return_value=None)
        view.expand_options = ['a', 'b']
        self.assertIsNone(getattr(view, '_validate_called', None))

        valid_options = ['a', 'b', 'a,b']
        invalid_options = ['1', 'c']

        for expand in valid_options:
            mock_request.args = {'expand': expand}
            self.assertEqual({}, view._validate())

        error = {
            'invalid-params': 'expand',
            'title': 'De waarde van expand wordt niet geaccepteerd',
            'detail': f'De mogelijke waarden zijn: a,b'
        }

        for expand in invalid_options:
            mock_request.args = {'expand': expand}
            self.assertEqual(error, view._validate())

    def test_validate_call_request_args(self):
        view = StufRestView()
        view._validate_request_args = MagicMock(return_value={'the': 'errors'})

        self.assertEqual({'the': 'errors'}, view._validate(kw='arg'))
        view._validate_request_args.assert_called_with(kw='arg')

    @patch("gobstuf.rest.brp.base_view.request")
    def test_get_functional_query_parameters(self, mock_request):
        mock_request.args = {
            'a': 1,
            'b': '',
            'c': None,
            'd': False,
        }
        view = StufRestView()
        view._transform_query_parameter_value = lambda x: x
        view.functional_query_parameters = {
            'a': 15,
            'b': 16,
            'c': 17,
            'd': 18,
            'e': 19
        }

        self.assertEqual({
            **mock_request.args,
            'e': 19,
        }, view._get_functional_query_parameters())

    @patch("gobstuf.rest.brp.base_view.g")
    @patch("gobstuf.rest.brp.base_view.request")
    @patch("gobstuf.rest.brp.base_view.StufErrorResponse")
    @patch("gobstuf.rest.brp.base_view.RESTResponse")
    def test_get(self, mock_rest_response, mock_response, mock_request, mock_g):
        g_attrs = {
            MKS_USER_KEY: 'user',
            MKS_APPLICATION_KEY: 'application',
        }
        mock_g.get = lambda x: g_attrs.get(x)
        mock_request.args = {}
        mock_request.headers = {
            'X-Correlation-ID': 'the correlation id'
        }

        mock_request_template = MagicMock()

        class StuffRestViewImpl(StufRestView):
            request_template = mock_request_template
            response_template = MagicMock()

        view = StuffRestViewImpl()
        view._make_request = MagicMock()
        view._error_response = MagicMock()
        view._json_response = MagicMock()
        view._validate_called = True
        view._get_functional_query_parameters = MagicMock(return_value={'funcparam': True})

        # Success response
        self.assertEqual(mock_rest_response.ok.return_value, view._get(a=1, b=2))
        view.request_template.assert_called_with('user', 'application', correlation_id='the correlation id')
        view.request_template.return_value.set_values.assert_called_with({'a': 1, 'b': 2})
        view._make_request.assert_called_with(view.request_template.return_value)

        view.response_template.assert_called_with(view._make_request.return_value.text, a=1, b=2, funcparam=True, wildcards={})
        mock_rest_response.ok.assert_called_with(view.response_template.return_value.get_answer_object.return_value)

        # Error response
        view._make_request.return_value.raise_for_status.side_effect = HTTPError
        self.assertEqual(view._error_response.return_value, view._get(a=1, b=2))
        mock_response.assert_called_with(view._make_request.return_value.text)
        view._error_response.assert_called_with(mock_response.return_value)

        # 404 response
        view._make_request = MagicMock()
        view.response_template.return_value.get_answer_object.side_effect = NoStufAnswerException
        view._not_found_response = MagicMock()

        self.assertEqual(mock_rest_response.not_found(), view._get(a=1, b=2))

        # Test invalid request
        view._validate = lambda **kwargs: {'some': 'error'}
        kwargs = {'kw': 'args'}
        self.assertEqual(mock_rest_response.bad_request.return_value, view.get(**kwargs))
        mock_rest_response.bad_request.assert_called_with(some='error')

    @patch("gobstuf.rest.brp.base_view.RESTResponse")
    def test_get_internal_server_error(self, mock_rest_response):
        view = StufRestView()
        view._get = MagicMock()
        view._validate = MagicMock(return_value={})
        view._get_functional_query_parameters = MagicMock(return_value={})
        view._validate_called = True
        view._validate_request_args = MagicMock(return_value=None)

        # Regular response
        result = view.get(any='thing')
        self.assertEqual(result, view._get.return_value)

        # Request failed for an unknown reason
        view._get.side_effect = Exception
        result = view.get(any='thing')
        self.assertEqual(result, mock_rest_response.internal_server_error.return_value)

        view._validate.side_effect = StufRestFilterView.InvalidQueryParametersException({'any': 'error'})
        view.get(any='thing')
        mock_rest_response.bad_request.assert_called_with(any='error')


class StufRestFilterViewImpl(StufRestFilterView):
    name = 'stufrestfilterviewobjects'


class TestStufRestFilterView(TestCase):

    def test_request_template_parameters(self):
        view = StufRestFilterViewImpl()
        view._get_query_parameters = lambda: {'e': 'f'}
        kwargs = {'a': 'b', 'c': 'd'}
        self.assertEqual({
            'a': 'b', 'c': 'd', 'e': 'f'
        }, view._request_template_parameters(**kwargs))

    @patch("gobstuf.rest.brp.base_view.StufRestView._validate")
    def test_validate(self, mock_parent_validate):
        view = StufRestFilterViewImpl()

        view._query_parameters_error = MagicMock()
        view._get_query_parameters = MagicMock()
        view._validate_called = True

        # Test parent validate errors
        mock_parent_validate.return_value = {'some': 'error'}
        self.assertEqual(mock_parent_validate.return_value, view._validate())

        # Test validation of query params
        mock_parent_validate.return_value = {}
        view.query_parameter_combinations = [
            ('a', 'b', 'c'),
            ('a', 'd'),
        ]

        # Test success
        view._get_query_parameters.return_value = {'a': 1, 'd': 2}
        self.assertEqual({}, view._validate())

        view._get_query_parameters.return_value = {'a': 1, 'b': 2}
        self.assertEqual({}, view._validate(c=3))

        # Test error
        view._get_query_parameters.side_effect = view.InvalidQueryParametersException
        self.assertEqual(view._query_parameters_error.return_value, view._validate())

    def test_query_parameters_error(self):
        view = StufRestFilterViewImpl()
        view.query_parameter_combinations = [
            ('a', 'b'),
            ('c', 'd'),
            (),
        ]

        self.assertEqual({
            'title': 'De opgegeven combinatie van parameters is niet correct',
            'detail': 'De mogelijke combinaties zijn: a / b , c / d , no params',
            'code': 'paramsRequired',
        }, view._query_parameters_error())

    @patch("gobstuf.rest.brp.base_view.RESTResponse")
    def test_build_response(self, mock_rest_response):
        view = StufRestFilterViewImpl()
        response_obj = MagicMock()
        response_obj.get_all_answer_objects = lambda: [{'object': 'A'}, {'object': 'B'}]

        self.assertEqual(mock_rest_response.ok.return_value, view._build_response(response_obj))
        mock_rest_response.ok.assert_called_with({
            '_embedded': {
                'stufrestfilterviewobjects': [
                    {'object': 'A'},
                    {'object': 'B'},
                ]
            }
        }, {})

    def test_transform_query_parameter_value(self):
        view = StufRestFilterViewImpl()
        some_mock = MagicMock()

        test_cases = [
            (None, None),
            ('', None),
            ('null', None),
            ('none', None),
            ('true', True),
            ('false', False),
            ('13', '13'),
            (True, True),
            (False, False),
            (11, 11),
            (some_mock, some_mock),
        ]

        for inp, outp in test_cases:
            self.assertEqual(outp, view._transform_query_parameter_value(inp))

    @patch("gobstuf.rest.brp.base_view.request")
    def test_get_query_parameters(self, mock_request):
        view = StufRestFilterViewImpl()

        # Default case. All parameters present, return first match
        mock_request.args = {
            'a': '1',
            'b': '2',
            'c': '3',
        }
        view.query_parameter_combinations = [
            ('a', 'b')
        ]
        self.assertEqual({'a': '1', 'b': '2'}, view._get_query_parameters())

        # Case with no parameters, allowed
        view.query_parameter_combinations = [()]
        mock_request.args = {}
        self.assertEqual({}, view._get_query_parameters())

        # Case with no parameters, not allowed
        view.query_parameter_combinations = []

        with self.assertRaises(view.InvalidQueryParametersException):
            view._get_query_parameters()

        # Case with invalid combination of parameters. B is missing
        view.query_parameter_combinations = [('a', 'b')]
        mock_request.args = {'a': '1'}

        with self.assertRaises(view.InvalidQueryParametersException):
            view._get_query_parameters()

        # Case with valid combination, plus two out of three optional query params
        mock_request.args = {
            'a': '1',
            'b': '2',
            'd': '4',
            'e': '5'
        }
        view.query_parameter_combinations = [
            ('a', 'b'),
        ]
        view.optional_query_parameters = ['c', 'd', 'e']
        self.assertEqual({'a': '1', 'b': '2', 'd': '4', 'e': '5'}, view._get_query_parameters())

    @patch("gobstuf.rest.brp.base_view.RESTResponse")
    def test_argument_check(self, mock_rest_response):
        view = StufRestView()
        view._validate_request_args = MagicMock(return_value={'error': 'any error'})
        self.assertEqual(view.get(), mock_rest_response.bad_request.return_value)
        mock_rest_response.bad_request.assert_called_with(error='any error')

    @patch("gobstuf.rest.brp.base_view.request")
    def test_validate_request_args(self, mock_request):
        class StufRestViewImpl(StufRestView):
            request_template = MagicMock()

        mock_request.args = {
            'attr5': 'value5',
        }

        view = StufRestViewImpl()
        view._request_template_parameters = MagicMock(return_value={
            'attr1': 'value1',
            'attr2': 'value2',
            'attr3': 'value3',
            'attr4': 'value4',
            'attr6': 'aa*',
            'attr7': 'a*',
        })

        view.request_template.parameter_checks = {
            'attr1': {
                'check': lambda v: False,
                'msg': {
                    'the msg': 'oh oh',
                }
            },
            'attr2': {
                'check': lambda v: True,
                'msg': {
                    'the msg': 'this one will not be shown',
                }
            },
            'attr4': {
                'check': lambda v: False,
                'msg': {
                    'the msg': 'foute boel',
                }
            },
            'attr5': {
                'check': lambda v: False,
                'msg': {
                    'the msg': 'If this error shows up, all request args that are not request_template_parameters are correctly validated',
                }
            },
            'attr7': [{
                'check': lambda v: True,
                'msg': {
                    'the msg': 'this one will not be shown',
                }
            }]
        }

        # attr6 receives the wildcard check, for attr7 the check will be appended to the current checks
        view.request_template.parameter_wildcards = ['attr6', 'attr7']

        self.assertEqual({
            'invalid-params': [
                {'name': 'attr1', 'the msg': 'oh oh'},
                {'name': 'attr4', 'the msg': 'foute boel'},
                {'name': 'attr7', 'code': 'invalidWildcardLength', 'reason': 'Zoeken met een wildcard vereist minimaal 2 karakters exclusief de wildcards.'},
                {'name': 'attr5', 'the msg': 'If this error shows up, all request args that are not request_template_parameters are correctly validated'}
            ],
            'title': 'Een of meerdere parameters zijn niet correct.',
            'detail': 'De foutieve parameter(s) zijn: attr1, attr4, attr7, attr5.',
            'code': 'paramsValidation',
        }, view._validate_request_args(some='kwargs'))
        view._request_template_parameters.assert_called_with(some='kwargs')

