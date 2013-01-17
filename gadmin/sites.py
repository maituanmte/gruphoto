from django.contrib.admin.sites import AdminSite
from gadmin.forms import AdminAuthenticationForm
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils.text import capfirst
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse, NoReverseMatch
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from gevents.models import EventUser
from gauth.models import User
from django.db.models import Count
from gruphoto import json_http

class GAdminSite(AdminSite):
    login_form = AdminAuthenticationForm
    password_change_template = 'admin/registration/password_change_form.html'
    password_change_done_template = 'admin/registration/password_change_done.html'
    
    def check_dependencies(self):
        """
        Check that all things needed to run the admin have been correctly installed.

        The default implementation checks that LogEntry, ContentType and the
        auth context processor are installed.
        """
        from gadmin.models import LogEntry
        from django.contrib.contenttypes.models import ContentType

        if not LogEntry._meta.installed:
            raise ImproperlyConfigured("Put 'gadmin' in your "
                "INSTALLED_APPS setting in order to use the admin application.")
        if not ContentType._meta.installed:
            raise ImproperlyConfigured("Put 'django.contrib.contenttypes' in "
                "your INSTALLED_APPS setting in order to use the admin application.")
        if not ('django.contrib.auth.context_processors.auth' in settings.TEMPLATE_CONTEXT_PROCESSORS or
            'django.core.context_processors.auth' in settings.TEMPLATE_CONTEXT_PROCESSORS):
            raise ImproperlyConfigured("Put 'django.contrib.auth.context_processors.auth' "
                "in your TEMPLATE_CONTEXT_PROCESSORS setting in order to use the admin application.")

    @never_cache
    def index(self, request, extra_context=None):
        """
        Displays the main admin index page, which lists all of the installed
        apps that have been registered in this site.
        """
        high_user_list = User.objects.filter(is_active=True, is_superuser=False).order_by('num_reports', 'num_blocked_event')[:25]
        abused_user_list = []
        for user in high_user_list:
            if user.num_reports > 0:
                item = {}
                item['user_id'] = user.id
                item['num_blocked_event'] = user.num_blocked_event
                item['num_reports'] = user.num_reports
                item['user'] = user
                item['level'] = user.level
                abused_user_list.append(item)

        # Sort the apps alphabetically.
        abused_user_list.sort(key=lambda x: -x['num_reports'])

        context = {
            'title': _('Dashboard'),
            'abused_user_list': abused_user_list,
            }

        context.update(extra_context or {})
        return TemplateResponse(request, [
            self.index_template or 'admin/index.html',
            ], context, current_app=self.name)
    
site = GAdminSite()
