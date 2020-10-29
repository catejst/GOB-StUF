from unittest import mock


def mock_getenv(varname, value=None):
    return varname


@mock.patch("os.getenv", mock_getenv)
def init():
    """
    Initialize StUF configuration so that every configuration variable
    has a default value equal to its own name
    :return: None
    """
    import gobstuf.config

init()
