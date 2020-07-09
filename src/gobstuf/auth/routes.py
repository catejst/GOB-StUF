import re

from flask import g, request, url_for

from gobcore.secure.config import AUTH_PATTERN, REQUEST_ROLES, REQUEST_USER

from gobstuf.config import INSECURE_PATH

REQUIRED_ROLE_PREFIX = 'fp_'
MKS_USER_KEY = 'MKS_GEBRUIKER'
MKS_APPLICATION_KEY = 'MKS_APPLICATIE'


def secure_route(rule, func):
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

    wrapper.__name__ = f"secure_{func.__name__}"
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


def _secure_headers_detected(rule, *args, **kwargs):
    """
    Check if any secure headers are present in the request

    :param rule:
    :param args:
    :param kwargs:
    :return:
    """
    for header, value in request.headers.items():
        if re.match(AUTH_PATTERN, header):
            return True
    return False


def _allows_access(rule, *args, **kwargs):
    """
    Check access to paths with variable catalog/collection names
    """
    role = _get_role()
    if role:
        # When a role is found store the MKS USER and APPLICATION in the global object and allow acces
        setattr(g, MKS_USER_KEY, role)
        setattr(g, MKS_APPLICATION_KEY, request.headers.get(REQUEST_USER, ""))
        return True
    else:
        return False


def _issue_fraud_warning(rule, *args, **kwargs):
    """
    Issue a fraud warning

    For now this is printed on stdout (to be found in Kibana)

    In the future this should be connected to an alert mechanism
    """
    print(f"ERROR: FRAUD DETECTED FOR RULE: {rule} => {request.url}", args, kwargs)
    dump_attrs = ['method', 'remote_addr', 'remote_user', 'headers']
    for attr in dump_attrs:
        print(attr, getattr(request, attr))


def public_route(rule, func, *args, **kwargs):
    """
    Public routes start with API_BASE_PATH and are not protected by gatekeeper

    The headers that are used to identify the user and/or role should NOT be present.
    If any of these headers are present that means that these headers are falsified
    The ip-address and any other identifying information should be reported

    :param func:
    :param args:
    :param kwargs:
    :return:
    """
    def wrapper(*args, **kwargs):

        if _secure_headers_detected(rule, *args, **kwargs):
            # Public route cannot contain secure headers
            _issue_fraud_warning(rule, *args, **kwargs)
            return "Bad request", 400
        else:
            # Set the MKS USER and APPLICATION in the global object if found in the headers
            setattr(g, MKS_USER_KEY, request.headers.get(MKS_USER_KEY))
            setattr(g, MKS_APPLICATION_KEY, request.headers.get(MKS_APPLICATION_KEY))
            return func(*args, **kwargs)

    wrapper.__name__ = f"public_{func.__name__}"
    return wrapper


def get_auth_url(view_name, **kwargs):
    wrapped_view_name = f"public_{view_name}" if INSECURE_PATH in request.base_url \
                                                else f"secure_{view_name}"
    url = url_for(wrapped_view_name, **kwargs)
    return f"{request.scheme}://{request.host}{url}"
