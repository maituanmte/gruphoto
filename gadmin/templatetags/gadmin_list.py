from django.contrib.admin.views.main import (ALL_VAR, EMPTY_CHANGELIST_VALUE,
                                             ORDER_VAR, PAGE_VAR, SEARCH_VAR)
from django.template import Library
register = Library()
@register.inclusion_tag('admin/search_form.html')
def search_form(cl):
    """
    Displays a search form for searching the list.
    """
    return {
        'cl': cl,
        'show_result_count': cl.result_count != cl.full_result_count,
        'search_var': SEARCH_VAR
    }