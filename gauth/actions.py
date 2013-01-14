from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.encoding import force_unicode
from django.contrib.admin.util import model_ngettext

def make_active(modeladmin, request, queryset):
    n = queryset.count()
    if n:
        for obj in queryset:
            obj_display = force_unicode(obj)
            modeladmin.log_change(request, obj, obj_display)
        queryset.update(is_active=True)
        modeladmin.message_user(request, _("Successfully updated %(count)d %(items)s as active.") % {
            "count": n, "items": model_ngettext(modeladmin.opts, n)
        })
    # Return None to display the change list page again.
    return None
make_active.short_description = _("Activate selected %(verbose_name_plural)s")
    
def make_disactive(modeladmin, request, queryset):
    n = queryset.count()
    if n:
        for obj in queryset:
            obj_display = force_unicode(obj)
            modeladmin.log_change(request, obj, obj_display)
        queryset.update(is_active=False)
        modeladmin.message_user(request, _("Successfully updated %(count)d %(items)s as disactive.") % {
            "count": n, "items": model_ngettext(modeladmin.opts, n)
        })
    # Return None to display the change list page again.
    return None
make_disactive.short_description = _("Disactivate selected %(verbose_name_plural)s")
