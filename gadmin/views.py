from django.shortcuts import render_to_response
from django.views.decorators.csrf import requires_csrf_token

@requires_csrf_token
def gpage_not_found(request, template_name='admin/g404.html'):
    return render_to_response(template_name=template_name)

@requires_csrf_token
def gserver_error(request, template_name='admin/g500.html'):
    return render_to_response(template_name=template_name)