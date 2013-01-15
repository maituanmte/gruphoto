from django.conf import settings
from django.shortcuts import HttpResponse
import json

DEFAULT_MIMETYPE = JSON_MIMETYPE = "application/json"

def save_file(file, upload_to=''):
    if not file:
        return ''

    filename = file._get_name()
    fd = open('%s/%s' % (settings.MEDIA_ROOT, str(upload_to)+"/" + str(filename)), 'wb')
    for chunk in file.chunks():
        fd.write(chunk)
    fd.close()
    return str(upload_to)+"/" + str(filename)

def json_http(data):
    return HttpResponse(json.dumps(data), mimetype=DEFAULT_MIMETYPE)