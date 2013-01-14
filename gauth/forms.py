from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from gauth.models import User
from gadmin.widgets import AdminImageWidget
from django.contrib.admin.widgets import AdminSplitDateTime
from django.contrib.auth.hashers import UNUSABLE_PASSWORD, is_password_usable, get_hasher
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext, ugettext_lazy as _
from django.forms.util import flatatt
from django.contrib.auth.admin import UserAdmin

class ReadOnlyPasswordHashWidget(forms.Widget):
    def render(self, name, value, attrs):
        if hasattr(self, 'initial'):
            value = self.initial
        encoded = value

        if not is_password_usable(encoded):
            return "None"

        final_attrs = self.build_attrs(attrs)

        encoded = smart_str(encoded)

        if len(encoded) == 32 and '$' not in encoded:
            algorithm = 'unsalted_md5'
        else:
            algorithm = encoded.split('$', 1)[0]

        try:
            hasher = get_hasher(algorithm)
        except ValueError:
            summary = "<strong>Invalid password format or unknown hashing algorithm.</strong>"
        else:
            summary = ""
            for key, value in hasher.safe_summary(encoded).iteritems():
                summary += "<strong>%(key)s</strong>: %(value)s <br/>" % {"key": ugettext(key), "value": value}

        return mark_safe("<div%(attrs)s>%(summary)s</div>" % {"attrs": flatatt(final_attrs), "summary": summary})

    def _has_changed(self, initial, data):
        return False


class ReadOnlyPasswordHashField(forms.Field):
    widget = ReadOnlyPasswordHashWidget

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        super(ReadOnlyPasswordHashField, self).__init__(*args, **kwargs)

    def bound_data(self, value, initial):
        self.widget.initial = initial
        return initial

class AuthenticationForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    email = forms.CharField(label=_("Email"), max_length=100)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': _("Please enter a correct email and password. "
                           "Note that both fields are case-sensitive."),
        'no_cookies': _("Your Web browser doesn't appear to have cookies "
                        "enabled. Cookies are required for logging in."),
        'inactive': _("This account is inactive."),
    }

    def __init__(self, request=None, *args, **kwargs):
        """
        If request is passed in, the form will validate that cookies are
        enabled. Note that the request (a HttpRequest object) must have set a
        cookie with the key TEST_COOKIE_NAME and value TEST_COOKIE_VALUE before
        running this validation.
        """
        self.request = request
        self.user_cache = None
        super(AuthenticationForm, self).__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(email=email,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'])
            elif not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'])
        self.check_for_test_cookie()
        return self.cleaned_data

    def check_for_test_cookie(self):
        if self.request and not self.request.session.test_cookie_worked():
            raise forms.ValidationError(self.error_messages['no_cookies'])

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache
    
class UserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'duplicate_email': _("A user with that email already exists."),
    }
    
    email = forms.RegexField(label=_("Email"), max_length=30,
        regex=r'^[\w.@+-]+$',
        help_text = _("Required. 100 characters or fewer. Letters, digits"),
        error_messages = {'invalid': _("Email is not correct format.")})
    
    password = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput)
    
    first_name = forms.CharField(label=_("First Name"),
        widget=forms.TextInput,
        help_text = _("Optional."), required=False)
    
    last_name = forms.CharField(label=_("Last Name"),
        widget=forms.TextInput,
        help_text = _("Optional."), required=False)
    
    photo = forms.ImageField(help_text = _("Click on image to change."), widget=AdminImageWidget, required=False)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'photo')

    def clean_email(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    
    
    error_messages = {
        'duplicate_email': _("A user with that email already exists."),
    }
    
    email = forms.CharField(label=_("Email"), max_length=30, help_text = _("Email is readonly."), required=False)

    password = ReadOnlyPasswordHashField(label=_("Password"),
        help_text=_("Raw passwords are not stored, so there is no way to see "
                    "this user's password, but you can change the password "
                    "using <a href=\"password/\">this form</a>."), required=False)

    first_name = forms.CharField(label=_("First Name"),
        widget=forms.TextInput,
        help_text = _("Optional."), required=False)

    last_name = forms.CharField(label=_("Last Name"),
        widget=forms.TextInput,
        help_text = _("Optional."), required=False)

    is_active = forms.BooleanField(label=_('Active'), widget=forms.CheckboxInput, required=False)

    photo = forms.ImageField(help_text = _("Click on image to change."), widget=AdminImageWidget, required=False)

    last_login = forms.DateTimeField(label=_("Last Login"),
        widget=AdminSplitDateTime, required=False)


    first_login = forms.DateTimeField(label=_("First Login"),
        widget=AdminSplitDateTime, required=False)
    
    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields['password'].widget.attrs['readonly'] = True
            
#    def clean_email(self):
#        return self.instance.email

    def clean_password(self):
        return self.instance.password

    class Meta:
        model = User
    
    def save(self, commit=True):
        user = super(UserChangeForm, self).save(commit=False)
        user.set_password(self.clean_password)
        if commit:
            user.save()
        return user
