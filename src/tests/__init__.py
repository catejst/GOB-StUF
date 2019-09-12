from unittest import mock

@mock.patch("os.getenv", lambda varname, value=None: varname)
def init():
    """
    Initialize StUF configuration so that every configuration variable
    has a default value equal to its own name
    :return: None
    """
    import gobstuf.config

init()
