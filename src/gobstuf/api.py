import re
import uuid

import flask
from flask import Flask, Response
from flask_cors import CORS

from urllib.parse import urlsplit, urlunsplit, SplitResult

from gobcore.logging.audit_logger import AuditLogger

from gobstuf.config import GOB_STUF_PORT, ROUTE_SCHEME, ROUTE_NETLOC, ROUTE_PATH
from gobstuf.certrequest import cert_get, cert_post
from werkzeug.exceptions import BadRequest, MethodNotAllowed, HTTPException


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

    if soap_action is None:
        raise BadRequest("Missing Soapaction in header")

    if "text/xml" not in content_type:
        raise BadRequest(f"Wrong content {content_type}; text/xml expected")

    headers = {
        "Soapaction": soap_action,
        "Content-Type": content_type
    }
    return cert_post(url, data=data, headers=headers)


def _handle_stuf_request(request, routed_url):
    method = request.method
    if method == 'GET':
        response = _get_stuf(routed_url)
    elif method == 'POST':
        data = _update_request(request.data.decode())
        response = _post_stuf(routed_url, data, request.headers)
    else:
        raise MethodNotAllowed(f"Unknown method {method}, GET or POST required")

    return response


def _stuf():
    """
    Handle StUF request

    :return: XML response
    """
    audit_logger = AuditLogger.get_instance()

    request = flask.request
    url = _routed_url(request.url)

    request_uuid = str(uuid.uuid4())

    request_log_data = {
        'soapaction': request.headers.get('Soapaction'),
        'original_url': request.url,
        'method': request.method,
    }
    audit_logger.log_request(request.remote_addr, url, request_log_data, request_uuid)

    response_log_data = {**request_log_data}

    try:
        response = _handle_stuf_request(request, url)
    except HTTPException as e:
        # If Exception occurs, log exception and re-raise
        response_log_data['exception'] = str(e)
        audit_logger.log_response(request.remote_addr, url, response_log_data, request_uuid)
        raise e

    # Successful
    response_log_data['remote_response_code'] = response.status_code
    audit_logger.log_response(request.remote_addr, url, response_log_data, request_uuid)
    text = _update_response(response.text)

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
