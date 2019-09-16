import re

import flask
from flask import Flask, Response
from flask_cors import CORS

from urllib.parse import urlsplit, urlunsplit, SplitResult

from gobstuf.config import GOB_STUF_PORT, ROUTE_SCHEME, ROUTE_NETLOC, ROUTE_PATH
from gobstuf.certrequest import cert_get, cert_post


def _health():
    """

    :return: Message telling the StUF API is OK
    """
    return 'Connectivity OK'


def _routed_url(url):
    """
    Transforms an url so that it directs to the underlying SOAP API endpoint

    :param url: url to transform, normally url of our own endpoint
    :return: the transformed url that points to the underlying SOAP API
    """
    split_result = urlsplit(url)
    split_result = SplitResult(scheme=ROUTE_SCHEME,
                               netloc=ROUTE_NETLOC,
                               path=split_result.path,
                               query=split_result.query,
                               fragment=split_result.fragment)
    routed_url = urlunsplit(split_result)

    # The root wsdl should be requested as a parameter to the url path
    routed_url = routed_url.replace(r"/?wsdl", r"?wsdl")
    return routed_url


def _update_response(text):
    """
    Update any response from the underlying SOAP API so that
    the address of the underlying api (domain + optional port number) is changed to the address
    of this StUF API

    :param text: any text, normally a XML string
    :return: the text where any reference to the underlying SOAP API is changed to ourself
    """
    pattern = ROUTE_NETLOC + r"(:\d{2,5})?"
    return re.sub(pattern, f"localhost:{GOB_STUF_PORT}", text)


def _update_request(text):
    """
    Update any request data for the underlying SOAP API so that
    the address of this StUF API is changed to the address of the underlying api (domain + optional port number)

    :param text: any text, normally a XML string
    :return: the text where any reference to ourself is changed to the underlying SOAP API
    """
    pattern = f"localhost:{GOB_STUF_PORT}"
    return re.sub(pattern, ROUTE_NETLOC, text)


def _get_stuf(url):
    """
    Get the StUF response from the given url

    :param url: url of SOAP endpoint of underlying SOAP server
    :return: response object
    """
    return cert_get(url)


def _post_stuf(url, data, headers):
    """
    Post the data to the given url

    :param url: url of SOAP endpoint of underlying SOAP server
    :param data: XML message contents
    :param headers: incoming request headers
    :return: response object
    """
    soap_action = headers.get("Soapaction")
    content_type = headers.get("Content-Type", "")
    assert soap_action is not None, "Missing Soapaction in header"
    assert "text/xml" in content_type, f"Wrong content {content_type}; text/xml expected"

    headers = {
        "Soapaction": soap_action,
        "Content-Type": content_type
    }
    return cert_post(url, data=data, headers=headers)


def _stuf():
    """
    Handle StUF request

    :return: XML response
    """
    request = flask.request

    method = request.method
    assert method in ['GET', 'POST'], f"Unknown method {method}, GET or POST required"

    url = _routed_url(request.url)
    if method == 'GET':
        response = _get_stuf(url)
    elif method == 'POST':
        data = _update_request(request.data.decode())
        response = _post_stuf(url, data, request.headers)

    text = response.text
    text = _update_response(text)

    return Response(text, mimetype="text/xml")


def get_app():
    """
    Initializes the Flask App that serves the SOAP endpoint(s)

    :return: Flask App
    """
    ROUTES = [
        # Health check URL
        ('/status/health/', _health, ['GET']),

        # StUF endpoints
        (f'{ROUTE_PATH}', _stuf, ['GET', 'POST']),
        (f'{ROUTE_PATH}/', _stuf, ['GET', 'POST']),
    ]

    print(f"StUF endpoint: localhost:{GOB_STUF_PORT}{ROUTE_PATH}")

    app = Flask(__name__)
    CORS(app)

    for route, view_func, methods in ROUTES:
        app.route(rule=route, methods=methods)(view_func)

    return app


def run():
    """
    Get the Flask app and run it at the port as defined in config

    :return: None
    """
    app = get_app()
    app.run(port=GOB_STUF_PORT)
