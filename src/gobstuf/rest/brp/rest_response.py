"""
Formatting of all REST responses

"""
import json

from flask import Response, request
from flask_api import status as http_status


class RESTResponse():

    @classmethod
    def _json_response(cls, data, **kwargs):
        """
        JSON response

        :param data:
        :param kwargs:
        :return:
        """
        return Response(response=json.dumps(data), **kwargs)

    @classmethod
    def _client_error_response(cls, data, status, **kwargs):
        """
        Assert that every error response has the required fields

        Format the type to refer to the w3org status code specification

        :param data:
        :param status:
        :param kwargs:
        :return:
        """
        status_info = {
            400: {'code': 'badRequest',     'description': 'Bad Request',           'sec': '10.4.1'},
            401: {'code': 'authentication', 'description': 'Unauthorized',          'sec': '10.4.2'},
            403: {'code': 'autorisation',   'description': 'Forbidden',             'sec': '10.4.4'},
            404: {'code': 'notFound',       'description': 'Not Found',             'sec': '10.4.5'},
            500: {'code': 'serverError',    'description': 'Internal Server Error', 'sec': '10.5.1'},
        }[status]

        sec = f'{status_info["sec"]} {status} {status_info["description"]}'
        data = {
            'type': f'https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec{sec}',
            'title': 'Client error.',
            'status': status,
            'detail': '',
            'instance': request.url,
            "code": status_info['code'],
            **data,
            **kwargs
        }
        return cls._json_response(data=data,
                                  content_type='application/problem+json',
                                  status=status,
                                  **kwargs)

    @classmethod
    def _hal(cls, data):
        """
        Add Hypertext Application Language links to the given data

        :param data:
        :return:
        """
        data['_links'] = {'self': {'href': request.url}}
        return data

    @classmethod
    def ok(cls, data):
        """
        An OK response returns the data in HAL JSON format

        :param data:
        :return:
        """
        hal_data = cls._hal(data)
        return cls._json_response(data=hal_data,
                                  content_type='application/hal+json',
                                  status=http_status.HTTP_200_OK)

    @classmethod
    def bad_request(cls, **kwargs):
        """
        Bad Request: The request could not be understood by the server due to malformed syntax

        :param kwargs:
        :return:
        """
        data = {
            'invalid-params': [],
            'title': 'Error occurred when requesting external system. See logs for more information.',
            'detail': 'The request could not be understood by the server due to malformed syntax. ' +
                      'The client SHOULD NOT repeat the request without modification.',
            **kwargs
        }
        return cls._client_error_response(data=data, status=http_status.HTTP_400_BAD_REQUEST)

    @classmethod
    def forbidden(cls, **kwargs):
        """
        Forbidden: The server understood the request, but is refusing to fulfill it

        :param kwargs:
        :return:
        """
        data = {
            'title': 'U bent niet geautoriseerd voor deze operatie.',
            'detail': 'The server understood the request, but is refusing to fulfill it.',
            **kwargs
        }
        return cls._client_error_response(data=data, status=http_status.HTTP_403_FORBIDDEN)

    @classmethod
    def not_found(cls, **kwargs):
        """
        Not Found: The server has not found anything matching the Request-URI

        :param kwargs:
        :return:
        """
        data = {
            'title': 'Opgevraagde resource bestaat niet.',
            'detail': 'The server has not found anything matching the Request-URI.',
            **kwargs
        }
        return cls._client_error_response(data=data, status=http_status.HTTP_404_NOT_FOUND)

    @classmethod
    def internal_server_error(cls, **kwargs):
        data = {
            "title": "Interne server fout.",
            "detail": "The server encountered an unexpected condition which prevented it from fulfilling the request.",
            **kwargs
        }
        return cls._client_error_response(data=data, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
