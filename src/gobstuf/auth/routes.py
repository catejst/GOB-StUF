from flask import g, request, url_for

from gobcore.secure.config import REQUEST_ROLES, REQUEST_USER


REQUIRED_ROLE_PREFIX = 'fp_'
MKS_USER_KEY = 'MKS_GEBRUIKER'
MKS_APPLICATION_KEY = 'MKS_APPLICATIE'


def secure_route(rule, func, name=None):
    """
    Secure routes are protected by gatekeeper

    The headers that are used to identify the user and/or role should be present

    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        # Check that the endpoint is protected by gatekeeper and check access
        if request.headers.get(REQUEST_USER) and request.headers.get(REQUEST_ROLES) and \
                _allows_access(rule, *args, **kwargs):
            return func(*args, **kwargs)
        else:
            return "Forbidden", 403

    wrapper.__name__ = func.__name__ if name is None else name
    return wrapper


def _get_roles():
    """
    Gets the user roles from the request headers
    """
    try:
        return [h for h in request.headers.get(REQUEST_ROLES, "").split(",") if h]
    except AttributeError:
        return []


def _get_role():
    # Get the first active role which starts with 'fp_'
    roles = _get_roles()
    return next((role for role in roles if role.startswith(REQUIRED_ROLE_PREFIX)), None)


def _allows_access(rule, *args, **kwargs):
    """
    Check access to paths with variable catalog/collection names
    """
    role = _get_role()
    if role:
        # When a role is found store the MKS USER and APPLICATION in the global object and allow acces
        setattr(g, MKS_APPLICATION_KEY, role)
        setattr(g, MKS_USER_KEY, request.headers.get(REQUEST_USER, ""))
        return True
    else:
        return False


def get_auth_url(view_name, **kwargs):
    url = url_for(view_name, **kwargs)
    return f"{request.scheme}://{request.host}{url}"
