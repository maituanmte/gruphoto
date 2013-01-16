from django.db import models
from django.contrib.auth.models import UserManager, _user_get_all_permissions
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.mail import send_mail
import urllib
from django.utils.encoding import smart_str
from django.contrib import auth
from django.contrib.auth.hashers import (
    check_password, make_password, is_password_usable)

from gauth.signals import user_logged_in
from django.utils.crypto import get_random_string

FOLLOWER = 0
FRIEND = 1

NONE = 0
LOWER = 1
MIDDLE = 2
HIGH = 3
ALERT_LEVEL = (
    (NONE, 'None'),
    (LOWER, 'Lower'),
    (MIDDLE, 'Middle'),
    (HIGH, 'High')
)

def update_last_login(sender, user, **kwargs):
    """
    A signal receiver which updates the last_login date for
    the user logging in.
    """
    user.last_login = timezone.now()
    user.save()
user_logged_in.connect(update_last_login)

class GUserManager(UserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given username must be set')
        email = UserManager.normalize_email(email)
        user = self.model(email=email,
                          is_staff=False, is_active=True, is_superuser=False,
                          last_login=now, first_login=now)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        u = self.create_user(email, password)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u

    def make_random_password(self, length=30,
                             allowed_chars='abcdefghjkmnpqrstuvwxyz'
                                           'ABCDEFGHJKLMNPQRSTUVWXYZ'
                                           '23456789'):
        """
        Generates a random password with the given length and given
        allowed_chars. Note that the default value of allowed_chars does not
        have "I" or "O" or letters and digits that look similar -- just to
        avoid confusion.
        """
        return get_random_string(length, allowed_chars)

class User(models.Model):
    email = models.EmailField(null=True, blank=True)
    password = models.CharField(_('password'), max_length=128,null=True, blank=True)
    first_name = models.CharField(null=True, blank=True, max_length=45)
    last_name = models.CharField(null=True, blank=True, max_length=45)
    photo = models.ImageField(upload_to='user', null=True, blank=True, default='user/default-avatar.png')
    num_like = models.IntegerField(_('number of likes'), default=0)
    num_follower = models.IntegerField(_('number of followers'), default=0)
    num_photo = models.IntegerField(_('number of photos'), default=0)
    num_event = models.IntegerField(_('number of events'), default=0)
    num_reports = models.IntegerField(default=0)
    level = models.IntegerField(default=NONE, choices=ALERT_LEVEL)
    social_id= models.CharField(blank=True, null=True, max_length=300)
    device_token = models.CharField(null=True, blank=True, max_length=300)
    user_token = models.CharField(null=True, blank=True, max_length=300)
    last_login = models.DateTimeField(_('last login'), default=timezone.now)
    first_login = models.DateTimeField(_('first login'), default=timezone.now)
    first_join = models.BooleanField(_('first join'), default=False)
    friend = models.ManyToManyField('self', symmetrical=False, related_name='friends+', through='UserFriend')
    
    is_active = models.BooleanField(_('active'), default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    objects = GUserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __unicode__(self):
        return self.full_name() or self.email

    def natural_key(self):
        return (self.email,)

    def get_absolute_url(self):
        return "/user/%s/" % urllib.quote(smart_str(self.id))


    def is_anonymous(self):
        """
        Always returns False. This is a way of comparing User objects to
        anonymous users.
        """
        return False

    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    def full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()
    full_name.allow_tags = True

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw_password):
            self.set_password(raw_password)
            self.save()
        return check_password(raw_password, self.password, setter)

    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.password = make_password(None)

    def has_usable_password(self):
        return is_password_usable(self.password)

    def get_group_permissions(self, obj=None):
        """
        Returns a list of permission strings that this user has through his/her
        groups. This method queries all available auth backends. If an object
        is passed in, only permissions matching this object are returned.
        """
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, "get_group_permissions"):
                if obj is not None:
                    permissions.update(backend.get_group_permissions(self,
                                                                     obj))
                else:
                    permissions.update(backend.get_group_permissions(self))
        return permissions

    def get_all_permissions(self, obj=None):
        return _user_get_all_permissions(self, obj)

    def has_perm(self, perm, obj=None):
        """
        Returns True if the user has the specified permission. This method
        queries all available auth backends, but returns immediately if any
        backend returns True. Thus, a user who has permission from a single
        auth backend is assumed to have permission in general. If an object is
        provided, permissions for this specific object are checked.
        """

        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        # Otherwise we need to check the backends.
        return False

    def has_perms(self, perm_list, obj=None):
        """
        Returns True if the user has each of the specified permissions. If
        object is passed, it checks if the user has all required perms for this
        object.
        """
        for perm in perm_list:
            if not self.has_perm(perm, obj):
                return False
        return True

    def has_module_perms(self, app_label):
        """
        Returns True if the user has any permissions in the given app label.
        Uses pretty much the same logic as has_perm, above.
        """
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        return False

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])
    
class UserFriend(models.Model):
    user = models.ForeignKey(User, related_name='user+')
    friend = models.ForeignKey(User, related_name='friend+')
    type = models.IntegerField(default=FOLLOWER)
    

