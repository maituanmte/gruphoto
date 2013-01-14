from warnings import warn
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from gauth.signals import user_logged_in, user_logged_out

SESSION_KEY = '_auth_user_token'
FRONTEND_SESSION_KEY = '_auth_user_frontend'
REDIRECT_FIELD_NAME = 'next'

def load_frontend(path):
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing authentication frontend %s: "%s"' % (path, e))
    except ValueError, e:
        raise ImproperlyConfigured('Error importing authentication frontends. Is AUTHENTICATION_FRONTENDS a correctly defined list or tuple?')
    try:
        cls = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" authentication frontend' % (module, attr))

    if not hasattr(cls, 'supports_inactive_user'):
        warn("Authentication frontends without a `supports_inactive_user` attribute are deprecated. Please define it in %s." % cls,
            DeprecationWarning)
        cls.supports_inactive_user = False
    return cls()

def get_frontends():
    from django.conf import settings
    frontends = []
    for frontend_path in settings.AUTHENTICATION_FRONTENDS:
        frontends.append(load_frontend(frontend_path))
    if not frontends:
        raise ImproperlyConfigured('No authentication frontends have been defined. Does AUTHENTICATION_FRONTENDS contain anything?')
    return frontends

def authenticate(**credentials):
    """
    If the given credentials are valid, return a User object.
    """
    for frontend in get_frontends():
        try:
            user = frontend.authenticate(**credentials)
        except TypeError:
            # This frontend doesn't accept these credentials as arguments. Try the next one.
            continue
        if user is None:
            continue
            # Annotate the user object with the path of the frontend.
        user.frontend = "%s.%s" % (frontend.__module__, frontend.__class__.__name__)
        return user

def login(request, user):
    """
    Persist a user id and a frontend in the request. This way a user doesn't
    have to reauthenticate on every request. Note that data set during
    the anonymous session is retained when the user logs in.
    """
    if user is None:
        user = request.user
        # TODO: It would be nice to support different login methods, like signed cookies.
    if SESSION_KEY in request.session:
        if request.session[SESSION_KEY] != user.user_token:
            # To avoid reusing another user's session, create a new, empty
            # session if the existing session corresponds to a different
            # authenticated user.
            request.session.flush()
    else:
        request.session.cycle_key()
    request.session[SESSION_KEY] = user.user_token
    request.session[FRONTEND_SESSION_KEY] = user.frontend
    if hasattr(request, 'user'):
        request.user = user
    user_logged_in.send(sender=user.__class__, request=request, user=user)

def logout(request):
    """
    Removes the authenticated user's ID from the request and flushes their
    session data.
    """
    # Dispatch the signal before the user is logged out so the receivers have a
    # chance to find out *who* logged out.
    user = getattr(request, 'user', None)
    if hasattr(user, 'is_authenticated') and not user.is_authenticated():
        user = None
    user_logged_out.send(sender=user.__class__, request=request, user=user)

    request.session.flush()
    if hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

def get_user(request):
    from django.contrib.auth.models import AnonymousUser
    try:
        user_token = request.session[SESSION_KEY]
        frontend_path = request.session[FRONTEND_SESSION_KEY]
        frontend = load_frontend(frontend_path)
        user = frontend.get_user(user_token) or AnonymousUser()
    except KeyError:
        user = AnonymousUser()
    return user