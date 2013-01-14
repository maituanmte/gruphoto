from django import forms
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from django.utils.encoding import smart_str, force_unicode
from gauth.models import User

from gevents.models import Event

class LabelWidget(forms.Widget):
    def render(self, name, value, attrs):
        value = force_unicode(value)
        final_attrs = self.build_attrs(attrs)
        summary ="<strong>%s</strong>" %value
        return mark_safe("<div%(attrs)s>%(summary)s</div>" % {"attrs": flatatt(final_attrs), "summary": summary})

class LabelField(forms.Field):
    widget = LabelWidget

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        super(LabelField, self).__init__(*args, **kwargs)

class TimeLimitWidget(forms.Widget):
    def render(self, name, value, attrs):
        value = force_unicode(value)
        final_attrs = self.build_attrs(attrs)
        summary ="<strong>%s h</strong>" %value
        return mark_safe("<div%(attrs)s>%(summary)s</div>" % {"attrs": flatatt(final_attrs), "summary": summary})

class TimeLimitField(LabelField):
    widget = TimeLimitWidget

class YesNoWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs)
        if value:
            img = '<img alt="True" src="/static/admin/img/icon-yes.gif">'
        else:
            img = '<img alt="False" src="/static/admin/img/icon-no.gif">'

        return mark_safe("<div%(attrs)s>%(summary)s</div>" % {"attrs": flatatt(final_attrs), "summary": img})

class YesNoField(LabelField):
    widget = YesNoWidget

class UserWidget(LabelWidget):
    def render(self, name, value, attrs):
        try:
            user = User.objects.get(pk=int(value))
            return super(UserWidget, self).render(name, user.get_full_name(), attrs)
        except:
            return super(UserWidget, self).render(name, 'None', attrs)

class UserField(LabelField):
    widget = UserWidget

class DetailEventForm(forms.ModelForm):
    created_by = forms.CharField(label=_('Creator'), required=False)
    time_limit = TimeLimitField(label=_('Time limit'), required=False)
    is_public = YesNoField(label=_('Public'), required=False)
    num_likes = LabelField(label=_('Number of likes'), required=False)
    num_reports = LabelField(label=_('Number of reports'), required=False)
    is_active = forms.CheckboxInput()

    class Meta:
        model = Event
