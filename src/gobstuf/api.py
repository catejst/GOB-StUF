import re

from flask import Flask, request, Response
from flask_cors import CORS

from urllib.parse import urlsplit, urlunsplit, SplitResult

from gobstuf.config import GOB_STUF_PORT, ROUTE_SCHEME, ROUTE_NETLOC, ROUTE_PATH
from gobstuf.certrequest import cert_get, cert_post


def _health():
    return 'Connectivity OK'


def _routed_url(url):
    split_result = urlsplit(url)
    split_result = SplitResult(scheme=ROUTE_SCHEME,
                               netloc=ROUTE_NETLOC,
                               path=split_result.path,
                               query=split_result.query,
                               fragment=split_result.fragment)
    return urlunsplit(split_result)


def _update_response(text):
    pattern = ROUTE_NETLOC + r"(:\d{4})?"
    return re.sub(pattern, f"localhost:{GOB_STUF_PORT}", text)


def _get_stuf(url):
    return cert_get(url)


def _post_stuf(url):
    soap_action = request.headers.get("Soapaction")
    content_type = request.headers.get("Content-Type", "")
    assert soap_action is not None, "Missing Soapaction in header"
    assert "text/xml" in content_type, f"Wrong content {content_type}; text/xml expected"

    data = request.data
    headers = {
        "Soapaction": soap_action,
        "Content-Type": content_type
    }
    return cert_post(url, data, headers)


def _stuf():
    assert request.method in ['GET', 'POST'], f"Unknown method {request.method}, GET or POST required"

    url = _routed_url(request.url)
    if request.method == 'GET':
        response = _get_stuf(url)
    elif request.method == 'POST':
        response = _post_stuf(url)

    text = response.text
    text = _update_response(text)

    return Response(text, mimetype="text/xml")


def get_app():
    ROUTES = [
        # Health check URL
        ('/status/health/', _health, ['GET']),

        # StUF endpoints
        (f'{ROUTE_PATH}', _stuf, ['GET', 'POST']),
        (f'{ROUTE_PATH}/', _stuf, ['GET', 'POST']),
    ]

    app = Flask(__name__)
    CORS(app)

    for route, view_func, methods in ROUTES:
        app.route(rule=route, methods=methods)(view_func)

    return app


def run():
    app = get_app()
    app.run(port=GOB_STUF_PORT)
