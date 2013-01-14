from functools import wraps
from django.utils.decorators import available_attrs
from grouphoto import json_http
from grouphoto.errors import    POST_METHOD_ERROR, POST_METHOD_ERROR_MESSAGE, \
                                GET_METHOD_ERROR,GET_METHOD_ERROR_MESSAGE,\
                                ERROR_MESSAGE, ERROR_CODE,\
                                USER_NOT_FOUND, USER_NOT_FOUND_MESSAGE, \
                                EVENT_ID_NOT_SET, EVENT_CODE_NOT_SET_MESSAGE, \
                                FRIEND_ID_NOT_SET, FRIEND_ID_NOT_SET_MESSAGE, \
                                IMAGE_ID_NOT_SET, IMAGE_ID_NOT_SET_MESSAGE, \
                                USER_ID_NOT_SET, USER_ID_NOT_SET_MESSAGE, \
                                USER_TOKEN_NOT_SET, USER_TOKEN_NOT_SET_MESSAGE
from grouphoto.fields import FRIEND_ID, EVENT_ID, IMAGE_ID, USER_ID, USER_TOKEN

def require_http_post(func):
    @wraps(func, assigned=available_attrs(func))
    def inner(request, *args, **kwargs):
        if request.method != 'POST':
            response_data = {}
            response_data[ERROR_CODE] = POST_METHOD_ERROR
            response_data[ERROR_MESSAGE] = POST_METHOD_ERROR_MESSAGE
            return json_http(response_data)
        return func(request, *args, **kwargs)
    return inner

def require_http_get(func):
    @wraps(func, assigned=available_attrs(func))
    def inner(request, *args, **kwargs):
        if request.method != 'POST':
            response_data = {}
            response_data[ERROR_CODE] = GET_METHOD_ERROR
            response_data[ERROR_MESSAGE] = GET_METHOD_ERROR_MESSAGE
            return json_http(response_data)
        return func(request, *args, **kwargs)
    return inner

def login_require(func):
    @wraps(func, assigned=available_attrs(func))
    def inner(request, *args, **kwargs):
        response_data = {}
        if not request.POST.get(USER_TOKEN, ''):
            response_data[ERROR_CODE] = USER_TOKEN_NOT_SET
            response_data[ERROR_MESSAGE] = USER_TOKEN_NOT_SET_MESSAGE
            return json_http(response_data)
        elif not request.user.is_authenticated():
            response_data[ERROR_CODE] = USER_NOT_FOUND
            response_data[ERROR_MESSAGE] = USER_NOT_FOUND_MESSAGE
            return json_http(response_data)
        return func(request, *args, **kwargs)
    return inner


def event_id_require(func):
    @wraps(func, assigned=available_attrs(func))
    def inner(request, *args, **kwargs):
        if not request.POST.get(EVENT_ID, ''):
            response_data = {}
            response_data[ERROR_CODE] = EVENT_ID_NOT_SET
            response_data[ERROR_MESSAGE] = EVENT_CODE_NOT_SET_MESSAGE
            return json_http(response_data)
        return func(request, *args, **kwargs)
    return inner

def image_id_require(func):
    @wraps(func, assigned=available_attrs(func))
    def inner(request, *args, **kwargs):
        if not request.POST.get(IMAGE_ID, ''):
            response_data = {}
            response_data[ERROR_CODE] = IMAGE_ID_NOT_SET
            response_data[ERROR_MESSAGE] = IMAGE_ID_NOT_SET_MESSAGE
            return json_http(response_data)
        return func(request, *args, **kwargs)
    return inner

def friend_id_require(func):
    @wraps(func, assigned=available_attrs(func))
    def inner(request, *args, **kwargs):
        if not request.POST.get(FRIEND_ID, ''):
            response_data = {}
            response_data[ERROR_CODE] = FRIEND_ID_NOT_SET
            response_data[ERROR_MESSAGE] = FRIEND_ID_NOT_SET_MESSAGE
            return json_http(response_data)
        return func(request, *args, **kwargs)
    return inner

def user_id_require(func):
    @wraps(func, assigned=available_attrs(func))
    def inner(request, *args, **kwargs):
        if not request.POST.get(USER_ID, ''):
            response_data = {}
            response_data[ERROR_CODE] = USER_ID_NOT_SET
            response_data[ERROR_MESSAGE] = USER_ID_NOT_SET_MESSAGE
            return json_http(response_data)
        return func(request, *args, **kwargs)
    return inner


