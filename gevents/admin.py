from django.contrib import admin
from django.conf import settings
from django import forms
import gadmin
from gevents.models import Event
from django.utils.encoding import force_unicode
from gauth.actions import make_active, make_disactive
from django.shortcuts import get_object_or_404
from django.contrib.admin.models import ContentType
from django.contrib.admin.util import unquote
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse
from gevents.forms import DetailEventForm
from django.contrib.admin.templatetags.admin_static import static
from django.utils.decorators import method_decorator
from django.db import models, transaction, router
from django.views.decorators.csrf import csrf_protect
from gevents.models import Image, EventUser
from gcomments.models import Comment

csrf_protect_m = method_decorator(csrf_protect)

class EventAdmin(admin.ModelAdmin):
    object_history_template = 'admin/object_history.html'
    search_fields = ('title',)
    list_display = ('title','time_limit','created_date','modified_date','created_by','is_public','is_active')
    list_filter = ('is_active','is_public')
    actions = [make_active, make_disactive]
    readonly_fields = ('created_by','time_limit','num_likes', 'is_public' )

    fieldsets = (
        (None, {'fields': ('created_by', 'time_limit', 'is_public', 'num_likes', 'is_active')}),
        )

    detail_form = DetailEventForm

    @property
    def media(self):
        extra = '' if settings.DEBUG else '.min'
        js = [
            'core.js',
            'admin/RelatedObjectLookups.js',
            'jquery%s.js' % extra,
            'jquery.init.js',
            'tab.js',
            ]
        if self.actions is not None:
            js.append('actions%s.js' % extra)
        if self.prepopulated_fields:
            js.extend(['urlify.js', 'prepopulate%s.js' % extra])
        if self.opts.get_ordered_objects():
            js.extend(['getElementsBySelector.js', 'dom-drag.js' , 'admin/ordering.js'])
        return forms.Media(js=[static('admin/js/%s' % url) for url in js])

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        defaults.update({
            'form': self.detail_form,
            'fields': admin.util.flatten_fieldsets(self.fieldsets),
            })
        defaults.update(kwargs)
        return super(EventAdmin, self).get_form(request, obj, **defaults)
    
    def log_addition(self, request, obj):
        """
        Log that an object has been successfully added.

        The default implementation creates an admin LogEntry object.
        """
        from gadmin.models import LogEntry, ADDITION
        from django.contrib.contenttypes.models import ContentType
        from django.utils.encoding import force_unicode
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(obj).pk,
            object_id       = obj.pk,
            object_repr     = force_unicode(obj),
            action_flag     = ADDITION
        )

    def log_change(self, request, obj, message):
        """
        Log that an object has been successfully changed.

        The default implementation creates an admin LogEntry object.
        """
        from gadmin.models import LogEntry, CHANGE
        from django.contrib.contenttypes.models import ContentType
        from django.utils.encoding import force_unicode
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(obj).pk,
            object_id       = obj.pk,
            object_repr     = force_unicode(obj),
            action_flag     = CHANGE,
            change_message  = message
        )

    def log_deletion(self, request, obj, object_repr):
        """
        Log that an object will be deleted. Note that this method is called
        before the deletion.

        The default implementation creates an admin LogEntry object.
        """
        from gadmin.models import LogEntry, DELETION
        from django.contrib.contenttypes.models import ContentType
        LogEntry.objects.log_action(
            user_id         = request.user.id,
            content_type_id = ContentType.objects.get_for_model(self.model).pk,
            object_id       = obj.pk,
            object_repr     = object_repr,
            action_flag     = DELETION
        )

    def history_view(self, request, object_id, extra_context=None):
        "The 'history' admin view for this model."
        from gadmin.models import LogEntry

        model = self.model
        opts = model._meta
        app_label = opts.app_label
        action_list = LogEntry.objects.filter(
            object_id = object_id,
            content_type__id__exact = ContentType.objects.get_for_model(model).id
        ).select_related().order_by('action_time')
        # If no history was found, see whether this object even exists.
        obj = get_object_or_404(model, pk=unquote(object_id))
        context = {
            'title': _('Change history: %s') % force_unicode(obj),
            'action_list': action_list,
            'module_name': capfirst(force_unicode(opts.verbose_name_plural)),
            'object': obj,
            'app_label': app_label,
            'opts': opts,
            }
        context.update(extra_context or {})
        return TemplateResponse(request, self.object_history_template, context, current_app=self.admin_site.name)

    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, form_url='', extra_context=None):
        images = Image.objects.filter(event_id=object_id)
        memberfilters = EventUser.objects.filter(event_id=object_id, joined=True)
        members = []
        for filter in memberfilters:
            members.append(filter.user)
        more = {}
        more['images'] = images
        more['members'] = members
        return super(EventAdmin, self).change_view(request, object_id, form_url, more)

class ImageAdmin(admin.ModelAdmin):
    list_display = ('source',)
    change_form_template = 'admin/gevents/image_detail.html'

    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, form_url='', extra_context=None):
        comments = Comment.objects.filter(image_id=object_id)
        image = Image.objects.get(pk=object_id)
        more = {}
        more['comments'] = comments
        more['event'] = image.event
        return super(ImageAdmin, self).change_view(request, object_id, form_url, more)
    
gadmin.site.register(Event, EventAdmin)
gadmin.site.register(Image, ImageAdmin)