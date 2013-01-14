import getpass
import locale
import unicodedata
from django.conf import settings
from gauth import models as gauth_models
from gauth import models as gauth_app
from gauth.models import User
from django.db.models import signals

# From http://stackoverflow.com/questions/1466827/ --
#
# Prevent interactive question about wanting a superuser created.  (This code
# has to go in this otherwise empty "models" module so that it gets processed by
# the "syncdb" command during database creation.)
from django.contrib.auth import models as auth_models
from django.contrib.auth.management import create_superuser, create_permissions

signals.post_syncdb.disconnect(create_permissions,
    dispatch_uid = "django.contrib.auth.management.create_permissions")
signals.post_syncdb.disconnect(
    create_superuser,
    sender=auth_models,
    dispatch_uid='django.contrib.auth.management.create_superuser')


# Create our own test user automatically.

def create_supergrouphotouser(app, created_models, verbosity, db, **kwargs):
    from django.core.management import call_command

    if gauth_app.User in created_models and kwargs.get('interactive', True):
        msg = ("\nYou just installed Django's grouphoto auth system, which means you "
            "don't have any superusers defined.\nWould you like to create one "
            "now? (yes/no): ")
        confirm = raw_input(msg)
        while 1:
            if confirm not in ('yes', 'no'):
                confirm = raw_input('Please enter either "yes" or "no": ')
                continue
            if confirm == 'yes':
                call_command("createsuperuser", interactive=True, database=db)
            break
        
def get_system_username():
    """
    Try to determine the current system user's username.

    :returns: The username as a unicode string, or an empty string if the
        username could not be determined.
    """
    try:
        return getpass.getuser().decode(locale.getdefaultlocale()[1])
    except (ImportError, KeyError, UnicodeDecodeError):
        # KeyError will be raised by os.getpwuid() (called by getuser())
        # if there is no corresponding entry in the /etc/passwd file
        # (a very restricted chroot environment, for example).
        # UnicodeDecodeError - preventive treatment for non-latin Windows.
        return u''


def get_default_email(check_db=True):
    """
    Try to determine the current system user's username to use as a default.

    :param check_db: If ``True``, requires that the username does not match an
        existing ``auth.User`` (otherwise returns an empty string).
    :returns: The username, or an empty string if no username can be
        determined.
    """
    from gauth.management.commands.createsuperuser import (
        EMAIL_RE)
    default_email = get_system_username()
    try:
        default_email = unicodedata.normalize('NFKD', default_email)\
            .encode('ascii', 'ignore').replace(' ', '').lower()
        default_email+='@admin.com'
    except UnicodeDecodeError:
        return ''
    if not EMAIL_RE.match(default_email):
        return ''
    # Don't return the default username if it is already taken.
    if check_db and default_email:
        try:
            User.objects.get(email=default_email)
        except User.DoesNotExist:
            pass
        else:
            return ''
    return default_email

signals.post_syncdb.connect(create_supergrouphotouser,
    sender=gauth_models, dispatch_uid='common.models.create_testuser')
