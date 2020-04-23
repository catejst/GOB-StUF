from unittest import TestCase
from unittest.mock import patch, MagicMock

import json

from gobstuf.rest.brp.rest_response import RESTResponse

mock_response = MagicMock()
any_data = {"any": "data"}

mock_request = MagicMock()
mock_request.url = "any url"


@patch("gobstuf.rest.brp.rest_response.Response", mock_response)
@patch("gobstuf.rest.brp.rest_response.request", mock_request)
class TestRESTResponse(TestCase):

    def setUp(self) -> None:
        mock_response.reset_mock()
        mock_response.side_effect = lambda **kwargs: kwargs

    def test_json_response(self):
        # Return the data as a JSON string response
        result = RESTResponse._json_response(any_data)
        self.assertEqual(result['response'], json.dumps(any_data))

        # Include any other arguments in the Response
        result = RESTResponse._json_response(any_data, aap="noot")
        self.assertEqual(result['aap'], "noot")

    def test_client_error_response(self):
        result = RESTResponse._client_error_response(data=any_data, status=400)
        response = json.loads(result['response'])
        # Check if all required attributes are present in the response
        for attr in ['type', 'title', 'status', 'detail', 'instance', 'code']:
            self.assertTrue(attr in response)

        # Check if the type is correctly build
        self.assertEqual(response['type'], "https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.1 400 Bad Request")
        self.assertEqual(response['status'], 400)
        self.assertEqual(response['instance'], mock_request.url)

        # Check override of default fields
        result = RESTResponse._client_error_response(data=any_data, status=400, title='any title', any='other')
        response = json.loads(result['response'])
        self.assertEqual(response['title'], 'any title')
        self.assertEqual(response['any'], 'other')

    def test_hal(self):
        hal = RESTResponse._hal(any_data)
        self.assertEqual(hal, {'_links': {'self': {'href': 'any url'}}, 'any': 'data'})

    def test_ok(self):
        result = RESTResponse.ok(any_data)
        response = json.loads(result['response'])
        self.assertEqual(result['content_type'], 'application/hal+json')
        self.assertEqual(result['status'], 200)
        self.assertEqual(response, RESTResponse._hal(any_data))

    def test_errors(self):
        for method in ['bad_request', 'forbidden', 'not_found']:
            result = getattr(RESTResponse, method)(**any_data)
            self.assertEqual(result['content_type'], 'application/problem+json')
            response = json.loads(result['response'])
            for k, v in any_data.items():
                self.assertEqual(response[k], v)

    def test_bad_request(self):
        result = RESTResponse.bad_request()
        self.assertEqual(result['status'], 400)

    def test_forbidden(self):
        result = RESTResponse.forbidden()
        self.assertEqual(result['status'], 403)

    def test_not_found(self):
        result = RESTResponse.not_found()
        self.assertEqual(result['status'], 404)
