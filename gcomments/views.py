from gcomments.models import Comment
from gruphoto.decorator import require_http_post, login_require, image_id_require
from gruphoto.fields import PARENT_COMMENT_ID, CONTENT, COMMENT_ID, USER_ID, IMAGE_ID,\
    NUM_REPLY
from gruphoto.errors import NO_ERROR, ERROR_CODE, ERROR_MESSAGE, UNKNOWN_ERROR, UNKNOWN_ERROR_MESSAGE
from gruphoto import json_http

@login_require
@require_http_post
@image_id_require
def comment(request):
    parent_comment_id = request.POST.get(PARENT_COMMENT_ID, '') or 0
    content = request.POST.get(CONTENT, '')
    if not comment:
        return json_http(None)

    response_data = {ERROR_CODE:NO_ERROR}
    try:
        user = request.user
        image = request.image
        comment_obj = Comment(user_id=user.id, image_id=image.id)
        comment_obj.content = content
        comment_obj.parent = parent_comment_id
        comment_obj.save()
        image.num_comments += 1
        image.save()
        if parent_comment_id != 0:
            parent = Comment.objects.get(pk=parent_comment_id)
            parent.num_reply += 1
            parent.save()

        response_data[COMMENT_ID] =comment_obj.id
        response_data[USER_ID] = comment_obj.user_id
        response_data[IMAGE_ID] = comment_obj.image_id
        response_data[CONTENT] = comment_obj.content
        response_data[NUM_REPLY] = comment_obj.num_reply

    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE
    return  json_http(response_data)
