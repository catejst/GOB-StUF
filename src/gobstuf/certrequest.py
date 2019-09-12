from requests_pkcs12 import get, post

from gobstuf.config import PKCS12_FILENAME, PKCS12_PASSWORD


def cert_get(url):
    """
    Get request with certificate

    :param url: url to get
    :return: request response
    """
    print(f"CERT GET {url}")
    response = get(url,
                   pkcs12_filename=PKCS12_FILENAME,
                   pkcs12_password=PKCS12_PASSWORD)
    print(f"CERT RESPONSE {response.status_code}, {response.reason}")
    return response


def cert_post(url, data, headers=None):
    """
    Post request with certificate

    :param url: url to post
    :param data: data to post
    :param headers: optional headers
    :return: request response
    """
    print(f"CERT POST {url}")
    response = post(url,
                    data=data,
                    headers=headers or {},
                    pkcs12_filename=PKCS12_FILENAME,
                    pkcs12_password=PKCS12_PASSWORD)
    print(f"CERT RESPONSE {response.status_code}, {response.reason}")
    return response
