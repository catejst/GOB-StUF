import os


def _getenv(varname, default_value=None):
    value = os.getenv(varname, default_value)
    assert value, f"Environment variable '{varname}' not set or empty"
    print(f"{varname}='{value}'")
    return value


GOB_STUF_PORT = _getenv("GOB_STUF_PORT", 8165)
ROUTE_PATH = _getenv("ROUTE_PATH")
ROUTE_SCHEME = _getenv("ROUTE_SCHEME")
ROUTE_NETLOC = _getenv("ROUTE_NETLOC")
PKCS12_FILENAME = _getenv("PKCS12_FILENAME")
PKCS12_PASSWORD = _getenv("PKCS12_PASSWORD")
