import gauth
from gauth.models import User
from gevents.models import Event, Image
from gcomments.models import Comment
from django.utils.functional import SimpleLazyObject
from gruphoto import json_http
from gruphoto.errors import USER_NOT_FOUND, USER_NOT_FOUND_MESSAGE, USER_BLOCKED, USER_BLOCKED_MESSAGE, \
     FRIEND_NOT_FOUND, FRIEND_NOT_FOUND_MESSAGE, FRIEND_BLOCKED, FRIEND_BLOCKED_MESSAGE, \
     EVENT_NOT_FOUND, EVENT_NOT_FOUND_MESSAGE, EVENT_BLOCKED, EVENT_BLOCKED_MESSAGE, \
     IMAGE_NOT_FOUND, IMAGE_NOT_FOUND_MESSAGE, PARENT_COMMENT_NOT_FOUND, PARENT_COMMENT_NOT_FOUND_MESSAGE, \
     ERROR_MESSAGE, ERROR_CODE
from gruphoto.fields import USER_TOKEN, FRIEND_ID, IMAGE_ID, USER_ID, PARENT_COMMENT_ID, EVENT_ID



def get_user(request):
    if not hasattr(request, '_cached_user'):
        request._cached_user = gauth.get_user(request)
    return request._cached_user


class FrontendsRequestMiddleware(object):
    def process_request(self, request):
        assert hasattr(request, 'session'), "The Django authentication middleware requires session middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."
        response_data = {}

        user_token = request.POST.get(USER_TOKEN,'') or request.GET.get(USER_TOKEN,'')
        if user_token:
            try:
                user = User.objects.get(user_token=user_token)
                if not user.is_active:
                    response_data[ERROR_CODE] = USER_BLOCKED
                    response_data[ERROR_MESSAGE] = USER_BLOCKED_MESSAGE
                    return json_http(response_data)
                request.user = SimpleLazyObject(lambda: get_user(request))
            except User.DoesNotExist:
                response_data[ERROR_CODE] = USER_NOT_FOUND
                response_data[ERROR_MESSAGE] = USER_NOT_FOUND_MESSAGE
                return json_http(response_data)

        user_id = request.POST.get(USER_ID,'') or request.GET.get(USER_ID,'')
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                if not user.is_active:
                    response_data[ERROR_CODE] = USER_BLOCKED
                    response_data[ERROR_MESSAGE] = USER_BLOCKED_MESSAGE
                    return json_http(response_data)
            except User.DoesNotExist:
                response_data[ERROR_CODE] = USER_NOT_FOUND
                response_data[ERROR_MESSAGE] = USER_NOT_FOUND_MESSAGE
                return json_http(response_data)

        friend_id = request.POST.get(FRIEND_ID,'') or request.GET.get(FRIEND_ID,'')
        if friend_id:
            try:
                friend = User.objects.get(pk=friend_id)
                if not friend.is_active:
                    response_data[ERROR_CODE] = FRIEND_BLOCKED
                    response_data[ERROR_MESSAGE] = FRIEND_BLOCKED_MESSAGE
                    return json_http(response_data)
                request.friend = friend
            except User.DoesNotExist:
                response_data[ERROR_CODE] = FRIEND_NOT_FOUND
                response_data[ERROR_MESSAGE] = FRIEND_NOT_FOUND_MESSAGE
                return json_http(response_data)

        event_id = request.POST.get(EVENT_ID,'') or request.GET.get(EVENT_ID,'')
        if event_id:
            try:
                event = Event.objects.get(pk=event_id)
                if not event.is_active:
                    response_data[ERROR_CODE] = EVENT_BLOCKED
                    response_data[ERROR_MESSAGE] = EVENT_BLOCKED_MESSAGE
                    return json_http(response_data)
                request.event = event
            except Event.DoesNotExist:
                response_data[ERROR_CODE] = EVENT_NOT_FOUND
                response_data[ERROR_MESSAGE] = EVENT_NOT_FOUND_MESSAGE
                return json_http(response_data)

        image_id = request.POST.get(IMAGE_ID,'') or request.GET.get(IMAGE_ID,'')
        if image_id:
            try:
                image = Image.objects.get(pk=image_id)
                request.image = image
            except Image.DoesNotExist:
                response_data[ERROR_CODE] = IMAGE_NOT_FOUND
                response_data[ERROR_MESSAGE] = IMAGE_NOT_FOUND_MESSAGE
                return json_http(response_data)

        comment_id = request.POST.get(PARENT_COMMENT_ID,'') or request.GET.get(PARENT_COMMENT_ID,'')
        if comment_id:
            try:
                comment_parent = Comment.objects.get(pk=comment_id)
                request.comment_parent = comment_parent
            except Comment.DoesNotExist:
                response_data[ERROR_CODE] = PARENT_COMMENT_NOT_FOUND
                response_data[ERROR_MESSAGE] = PARENT_COMMENT_NOT_FOUND_MESSAGE
                return json_http(response_data)
