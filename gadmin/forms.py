from django import forms

from django.contrib.auth import authenticate
from gauth.forms import AuthenticationForm
from gauth.models import User

from django.utils.translation import ugettext_lazy

ERROR_MESSAGE = ugettext_lazy("Please enter the correct email and password "
        "for a staff account. Note that both fields are case-sensitive.")

class AdminAuthenticationForm(AuthenticationForm):

    this_is_the_login_form = forms.BooleanField(widget=forms.HiddenInput, initial=1,
        error_messages={'required': ugettext_lazy("Please log in again, because your session has expired.")})

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        message = ERROR_MESSAGE

        if email and password:
            self.user_cache = authenticate(email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(message)
            if not self.user_cache.is_active or not self.user_cache.is_staff:
                raise forms.ValidationError(message)
        self.check_for_test_cookie()
        return self.cleaned_data
