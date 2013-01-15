from django.contrib.auth.admin import UserAdmin
import gadmin
from gauth.models import User, AbuseReport
from django.contrib import admin
from gauth.forms import UserChangeForm, UserCreationForm
from django.utils.encoding import force_unicode
from django.contrib.admin.util import model_ngettext
from gauth.actions import make_active, make_disactive
from django.shortcuts import get_object_or_404
from django.contrib.admin.models import ContentType
from django.contrib.admin.util import unquote
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse
from functools import update_wrapper
from django.utils.safestring import mark_safe
from django.views.decorators.debug import sensitive_post_parameters
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext
from django.contrib import messages
from django.utils.html import escape
from django.contrib.auth.forms import AdminPasswordChangeForm

class GUserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    object_history_template = 'admin/object_history.html'
    change_form_template = 'admin/gauth/change_form.html'
    add_form_template = 'admin/gauth/change_form.html'
    change_user_password_template = 'admin/gauth/change_password.html'
    ajax_add_form_template = None
    ajax_change_form_template = None
    ajax_change_list_template = None
    list_per_page = 30
    readonly_fields = ('last_login', 'first_login')

    fieldsets = (
        (None, {'fields': ('photo', 'email', 'password', 'first_name', 'last_name', 'is_active' , 'last_login', 'first_login')}),
    )

    add_fieldsets = (
        (None, {'fields': ('photo', 'email', 'password', 'first_name', 'last_name', 'is_active')}),
    )

    filter_horizontal = ()
    search_fields = ('first_name', 'last_name', 'email')
    list_display = ('email', 'full_name', 'first_login', 'is_active', 'level' )
    list_filter = ('is_active','level')
    ordering = ('first_name', 'last_name',)
    actions = [make_active, make_disactive]

    def __init__(self, model, admin_site):
        self.is_ajax = False
        super(GUserAdmin, self).__init__(model, admin_site)

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return self.readonly_fields + ('email',)
        return super(GUserAdmin, self).get_readonly_fields(request, obj)

    def get_fieldsets(self, request, obj=None):
        if not obj:#
            return self.add_fieldsets
        return super(GUserAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults.update({
                'form': self.add_form,
                'fields': admin.util.flatten_fieldsets(self.add_fieldsets),
                })
        defaults.update(kwargs)
        return super(GUserAdmin, self).get_form(request, obj, **defaults)

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

    def queryset(self, request):
        qs = super(GUserAdmin, self).queryset(request)
        return qs.filter(is_superuser=0)

    @sensitive_post_parameters()
    def user_change_password(self, request, id, form_url=''):
        user = get_object_or_404(self.queryset(request), pk=id)
        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                msg = ugettext('Password changed successfully.')
                messages.success(request, msg)
                return HttpResponseRedirect('..')
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {'fields': form.base_fields.keys()})]
        adminForm = admin.helpers.AdminForm(form, fieldsets, {})

        context = {
            'title': _('Change password: %s') % escape(unicode(user)),
            'adminForm': adminForm,
            'form_url': mark_safe(form_url),
            'form': form,
            'is_popup': '_popup' in request.REQUEST,
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
            }
        return TemplateResponse(request, self.change_user_password_template, context, current_app=self.admin_site.name)

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

    def add_view(self, request, form_url='', extra_context=None):
        # It's an error for a user to have add permission but NOT change
        # permission for users. If we allowed such users to add users, they
        # could create superusers, which would mean they would essentially have
        # the permission to change users. To avoid the problem entirely, we
        # disallow users from adding users if they don't have change
        # permission.
        if extra_context is None:
            extra_context = {}
        defaults = {
            'auto_populated_fields': (),
            'username_help_text': self.model._meta.get_field('email').help_text,
            }
        extra_context.update(defaults)
        return admin.ModelAdmin.add_view(self, request, form_url,
            extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        from gauth.models import UserFriend
        followers_filters = UserFriend.objects.filter(friend_id=object_id)
        followers = []
        for follower in followers_filters:
            followers.append(follower.user)
        more = {}
        more['followers'] = followers
        more.update(extra_context or {})
        return super(GUserAdmin, self).change_view(request, object_id, form_url, more)

class AbusedEventAdmin(admin.ModelAdmin):
    search_fields = ('to', 'subject')
    list_display = ('user', 'reporter', 'to', 'subject',)
#    date_hierarchy = ('created_date',)

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

gadmin.site.register(AbuseReport, AbusedEventAdmin)
gadmin.site.register(User, GUserAdmin)