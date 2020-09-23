import os


def _getenv(varname, default_value=None, is_optional=False):
    """
    Returns the value of the environment variable "varname"
    or the default value if the environment variable is not set

    :param varname: name of the environment variable
    :param default_value: value to return if variable is not set
    :raises AssertionError: if variable not set or value is empty
    :return: the value of the given variable
    """
    value = os.getenv(varname, default_value)
    assert is_optional or value, f"Environment variable '{varname}' not set or empty"
    return value


# Required parameters
ROUTE_PATH_310 = _getenv("ROUTE_PATH_310")
ROUTE_PATH_204 = _getenv("ROUTE_PATH_204")
ROUTE_NETLOC = _getenv("ROUTE_NETLOC")

# Parameters with default value
GOB_STUF_PORT = _getenv("GOB_STUF_PORT", default_value=8165)
ROUTE_SCHEME = _getenv("ROUTE_SCHEME", default_value="https")

# Optional parameters
PKCS12_FILENAME = _getenv("PKCS12_FILENAME", is_optional=True)
PKCS12_PASSWORD = _getenv("PKCS12_PASSWORD", is_optional=True)

API_BASE_PATH = _getenv("BASE_PATH", default_value="", is_optional=True)
INSECURE_PATH = "/insecure"
API_INSECURE_BASE_PATH = f"{API_BASE_PATH}{INSECURE_PATH}"

AUDIT_LOG_CONFIG = {
    'EXEMPT_URLS': [],
    'LOG_HANDLER_CALLABLE_PATH': 'gobstuf.audit_log.get_log_handler',
    'USER_FROM_REQUEST_CALLABLE_PATH': 'gobstuf.audit_log.get_user_from_request'
}

CONTAINER_BASE = _getenv("CONTAINER_BASE", default_value="development")
BRP_REGRESSION_TEST_USER = _getenv("BRP_REGRESSION_TEST_USER")
BRP_REGRESSION_TEST_APPLICATION = _getenv("BRP_REGRESSION_TEST_APPLICATION")
GOB_OBJECTSTORE = 'GOBObjectstore'

CORRELATION_ID_HEADER = 'X-Correlation-ID'
UNIQUE_ID_HEADER = 'X-Unique-ID'

GELF_HOST = _getenv("GELF_HOST", is_optional=True)
GELF_PORT = _getenv("GELF_PORT", is_optional=True)
