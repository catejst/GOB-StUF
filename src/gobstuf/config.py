import os


def _getenv(varname, default_value=None):
    """
    Returns the value of the environment variable "varname"
    or the default value if the environment variable is not set

    :param varname: name of the environment variable
    :param default_value: value to return if variable is not set
    :raises AssertionError: if variable not set or value is empty
    :return: the value of the given variable
    """
    value = os.getenv(varname, default_value)
    assert value, f"Environment variable '{varname}' not set or empty"
    return value


GOB_STUF_PORT = _getenv("GOB_STUF_PORT", 8165)
ROUTE_PATH = _getenv("ROUTE_PATH")
ROUTE_SCHEME = _getenv("ROUTE_SCHEME")
ROUTE_NETLOC = _getenv("ROUTE_NETLOC")
PKCS12_FILENAME = _getenv("PKCS12_FILENAME")
PKCS12_PASSWORD = _getenv("PKCS12_PASSWORD")
