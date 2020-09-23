from requests_pkcs12 import get, post

from gobstuf.config import PKCS12_FILENAME, PKCS12_PASSWORD
from gobstuf.logger import get_default_logger


logger = get_default_logger()


def _add_cert_info(kwargs):
    """
    Update get/post arguments with any certificate info

    :param kwargs: dictionary with get/post arguments
    :return: The updated dictionary
    """
    if PKCS12_FILENAME:
        kwargs.update({
            'pkcs12_filename': PKCS12_FILENAME,
            'pkcs12_password': PKCS12_PASSWORD
        })
    return kwargs


def cert_get(url, **kwargs):
    """
    Get request with certificate

    :param url: url to get
    :return: request response
    """
    logger.info(f"GET {url}")
    kwargs = _add_cert_info(kwargs)
    response = get(url, **kwargs)
    logger.info(f"RESPONSE {response.status_code}, {response.reason}")
    return response


def cert_post(url, **kwargs):
    """
    Post request with certificate

    :param url: url to post
    :param data: data to post
    :param headers: optional headers
    :return: request response
    """
    logger.info(f"POST {url}")
    kwargs = _add_cert_info(kwargs)
    response = post(url, **kwargs)
    logger.info(f"RESPONSE {response.status_code}, {response.reason}")
    return response
