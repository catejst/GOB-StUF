from requests_pkcs12 import get, post

from gobstuf.config import PKCS12_FILENAME, PKCS12_PASSWORD


def cert_get(url):
    print(f"CERT GET {url}")
    response = get(url, pkcs12_filename=PKCS12_FILENAME, pkcs12_password=PKCS12_PASSWORD)
    print(f"CERT RESPONSE {response.status_code}, {response.reason}")
    return response


def cert_post(url, data, headers={}):
    print(f"CERT POST {url}")
    response = post(url, data=data, headers=headers, pkcs12_filename=PKCS12_FILENAME, pkcs12_password=PKCS12_PASSWORD)
    print(f"CERT RESPONSE {response.status_code}, {response.reason}")
    return response
