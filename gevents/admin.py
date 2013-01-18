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
from django.db import transaction
from django.views.decorators.csrf import csrf_protect
from gevents.models import Image, EventUser, AbuseReport
from gcomments.models import Comment
from django.http import Http404, HttpResponseRedirect
from django.utils.html import escape
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.core import urlresolvers

csrf_protect_m = method_decorator(csrf_protect)

class EventAdmin(admin.ModelAdmin):
    object_history_template = 'admin/object_history.html'
    search_fields = ('title','created_by__first_name', 'created_by__last_name')
    list_display = ('title','time_limit','created_date','modified_date','user_link','is_public')
    list_filter = ('is_public',)
    actions = [make_active, make_disactive]
    readonly_fields = ('user_link','time_limit','num_likes', 'is_public' , 'place_address', 'place_name')

    fieldsets = (
        (None, {'fields': ('user_link', 'time_limit', 'is_public', 'num_likes', 'place_address', 'place_name')}),
        )

    detail_form = DetailEventForm

    def user_link(self, obj):
        change_url = urlresolvers.reverse('admin:gauth_user_change', args=(obj.created_by.id,))
        return mark_safe(u'<a href="%s">%s</a>' % (change_url, obj.created_by))
    user_link.allow_tags = True
    user_link.short_description = 'Created by'

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

class AbusedEventAdmin(admin.ModelAdmin):
    search_fields = ('user__first_name', 'user__last_name', 'reporter__first_name', 'reporter__last_name', 'event__title')
    list_display = ('id', 'user_link', 'reporter_link','event_link', 'to', 'view')
    readonly_fields = ('to', 'cc', 'bcc', 'subject','reporter_link', 'user_link', 'event_link', 'content')
    exclude = ('user', 'event', 'reporter')

    def view(self, obj):
        url = reverse('admin:gevents_abusereport_change', args=(obj.pk,))
        return mark_safe(u'<a href="%s"><img src="/static/admin/img/view.png"></a>' % url)
    view.allow_tags = True
    view.short_description = 'View'

    def user_link(self, obj):
        change_url = urlresolvers.reverse('admin:gauth_user_change', args=(obj.user.id,))
        return mark_safe(u'<a href="%s">%s</a>' % (change_url, obj.user))
    user_link.allow_tags = True
    user_link.short_description = 'User'

    def reporter_link(self, obj):
        change_url = urlresolvers.reverse('admin:gauth_user_change', args=(obj.reporter.id,))
        return mark_safe(u'<a href="%s">%s</a>' % (change_url, obj.reporter))
    reporter_link.allow_tags = True
    reporter_link.short_description = 'Reporter'

    def event_link(self, obj):
        change_url = urlresolvers.reverse('admin:gevents_event_change', args=(obj.event.id,))
        return mark_safe(u'<a href="%s">%s</a>' % (change_url, obj.event))
    event_link.allow_tags = True
    event_link.short_description = 'Reporter'

    def get_urls(self):
        from django.conf.urls import patterns, url
        urls = super(AbusedEventAdmin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.module_name
        urlpatterns = patterns('',url(r'^(.+)/block/$', self.admin_site.admin_view(self.block_view), name='%s_%s_block' % info),)
        return  urlpatterns + urls

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

    @csrf_protect_m
    @transaction.commit_on_success
    def block_view(self, request, object_id):
        opts = self.model._meta
        obj = self.get_object(request, unquote(object_id))

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})
        from gevents.models import EventUser
        user = obj.user
        event = obj.event
        event_user, created = EventUser.objects.get_or_create(user=user, event=event)
        event_user.blocked = not event_user.blocked
        event_user.save()
        if event_user.blocked:
            user.num_blocked_event += 1
        else:
            user.num_blocked_event -= 1
        user.save()

        return HttpResponseRedirect(request.path.replace('block/',''))

    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, form_url='', extra_context=None):
        opts = self.model._meta
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})
        from gevents.models import EventUser
        user = obj.user
        event = obj.event
        event_user, created = EventUser.objects.get_or_create(user=user, event=event)
        more = {'blocked':event_user.blocked}

        more.update(extra_context or {})
        return super(AbusedEventAdmin, self).change_view(request, object_id, form_url, extra_context=more)

    
gadmin.site.register(Event, EventAdmin)
gadmin.site.register(Image, ImageAdmin)
gadmin.site.register(AbuseReport, AbusedEventAdmin)