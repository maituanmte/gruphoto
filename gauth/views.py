from gauth.models import User, UserFriend, AbuseReport, NONE, HIGH, MIDDLE, LOWER
from django.conf import settings
from gruphoto import save_file
from gruphoto import json_http
from gruphoto.errors import NO_ERROR, \
     WRONG_EMAIL, WRONG_EMAIL_MESSAGE, EMAIL_EXISTED, EMAIL_EXISTED_MESSAGE,\
     UNKNOWN_ERROR, UNKNOWN_ERROR_MESSAGE, ERROR_CODE, ERROR_MESSAGE, \
     WRONG_EMAIL_OR_PASSWORD, WRONG_EMAIL_OR_PASSWORD_MESSAGE,\
     USER_BLOCKED, USER_BLOCKED_MESSAGE,\
     DEVICE_TOKEN_NOT_SET, DEVICE_TOKEN_NOT_SET_MESSAGE
from gruphoto.fields import EMAIL, PASSWORD, FIRST_NAME, LAST_NAME, PHONE, PHOTO, USER_TOKEN, NUM_FOLLOWER, \
     NUM_LIKE, NUM_PHOTO, DEVICE_TOKEN, SOCIAL_ID, USER_ID, FOLLOWED, NUM_EVENT, TO, CC, BCC, REPORT_ID, CONTENT
import gauth
from gruphoto.decorator import require_http_post, login_require, friend_id_require, user_id_require

from django.contrib.auth.tokens import default_token_generator

IMAGE_DEFAULT = 'user/default-avatar.png'

@require_http_post
def register(request):
    email = request.POST.get(EMAIL, '')
    password = request.POST.get(PASSWORD, '')
    if not email or not password:
        return json_http(None)
    first_name = request.POST.get(FIRST_NAME, '')
    last_name = request.POST.get(LAST_NAME, '')
    phone = request.POST.get(PHONE, '')
    photo = request.FILES.get(PHOTO, '')
    device_token = request.POST.get(DEVICE_TOKEN, '')

    response_data = {ERROR_CODE:NO_ERROR}

    try:
        users = User.objects.filter(email=email)
        for user in users:
            if user.social_id:
                continue
            response_data[ERROR_CODE] = EMAIL_EXISTED
            response_data[ERROR_MESSAGE] = EMAIL_EXISTED_MESSAGE
            return  json_http(response_data)

        user = User.objects.create(email=email)

        user.set_password(password)
        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        photo_url = save_file(file=photo, upload_to='user')
        user.photo = photo_url or IMAGE_DEFAULT
        user.device_token = device_token
        user_token = default_token_generator.make_token(user)
        user.user_token = user_token
        user.save()

        user_login = gauth.authenticate(email=email, password=password)
        gauth.login(request, user_login)

        response_data[USER_TOKEN] = user_login.user_token
        response_data[USER_ID] = user_login.id
        response_data[FIRST_NAME] = user_login.first_name
        response_data[LAST_NAME] = user_login.last_name
        photo_link = ""
        if unicode(user_login.photo):
            photo_link = settings.MEDIA_URL + unicode(user_login.photo)
        response_data[PHOTO] = photo_link
        response_data[NUM_FOLLOWER] = user_login.num_follower
        response_data[NUM_LIKE] = user_login.num_like
        response_data[NUM_PHOTO] = user_login.num_photo
        response_data[SOCIAL_ID] = user_login.social_id
        response_data[DEVICE_TOKEN] = user_login.device_token

    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE
        return  json_http(response_data)


    response_data[USER_TOKEN] = user.user_token
    return  json_http(response_data)

@require_http_post
def login(request):
    email = request.POST.get(EMAIL, '')
    password = request.POST.get(PASSWORD, '')
    if not email or not password:
        return json_http(None)

    response_data = {ERROR_CODE:NO_ERROR}
    device_token = request.POST.get(DEVICE_TOKEN, '')
    try:
        user_login = gauth.authenticate(email=email, password=password)
        if user_login is None:
            response_data[ERROR_CODE] = WRONG_EMAIL_OR_PASSWORD
            response_data[ERROR_MESSAGE] = WRONG_EMAIL_OR_PASSWORD_MESSAGE
            return  json_http(response_data)

        user_token = default_token_generator.make_token(user_login)
        user_login.user_token = user_token
        user_login.save()

        gauth.login(request, user_login)
        user_login.device_token = device_token
        user_login.save()

        response_data[USER_TOKEN] = user_login.user_token
        response_data[USER_ID] = user_login.id
        response_data[FIRST_NAME] = user_login.first_name
        response_data[LAST_NAME] = user_login.last_name
        photo_link = unicode(user_login.photo) if '://' in unicode(user_login.photo) else settings.MEDIA_URL + unicode(user_login.photo)
        response_data[PHOTO] = photo_link
        response_data[NUM_FOLLOWER] = user_login.num_follower
        response_data[NUM_LIKE] = user_login.num_like
        response_data[NUM_PHOTO] = user_login.num_photo
        response_data[SOCIAL_ID] = user_login.social_id
        response_data[DEVICE_TOKEN] = user_login.device_token

    except User.DoesNotExist:
        response_data[ERROR_CODE] = WRONG_EMAIL

    return  json_http(response_data)

@require_http_post
def login_via_facebook(request):
    social_id = request.POST.get(SOCIAL_ID, '')
    if not social_id:
        return

    email = request.POST.get(EMAIL, '')
    photo = request.POST.get(PHOTO, '')
    first_name = request.POST.get(FIRST_NAME, '')
    last_name = request.POST.get(LAST_NAME, '')
    phone = request.POST.get(PHONE, '')
    device_token = request.POST.get(DEVICE_TOKEN, '')

    response_data = {ERROR_CODE:NO_ERROR}
    if not device_token:
        response_data[ERROR_CODE] = DEVICE_TOKEN_NOT_SET
        response_data[ERROR_MESSAGE] = DEVICE_TOKEN_NOT_SET_MESSAGE
        return  json_http(response_data)

    try:
        user, created = User.objects.get_or_create(social_id=social_id)
        user_token = User.objects.make_random_password()

        user.user_token = user_token
        user.email = email
        user.device_token = device_token
        user.photo = photo
        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        user.save()

        user_login = gauth.authenticate(user_token=user_token)
        gauth.login(request, user_login)

        response_data[USER_TOKEN] = user_login.user_token
        response_data[USER_ID] = user_login.id
        response_data[FIRST_NAME] = user_login.first_name
        response_data[LAST_NAME] = user_login.last_name
        response_data[PHOTO] = photo
        response_data[NUM_FOLLOWER] = user_login.num_follower
        response_data[NUM_LIKE] = user_login.num_like
        response_data[NUM_PHOTO] = user_login.num_photo
        response_data[SOCIAL_ID] = user_login.social_id
        response_data[DEVICE_TOKEN] = user_login.device_token
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE
        return json_http(response_data)

    return  json_http(response_data)

@require_http_post
def forgot_password(request):
    email = request.POST.get(EMAIL, '')
    if not email:
        return

    response_data = {ERROR_CODE:NO_ERROR}
    try:
        from django.utils.crypto import get_random_string
        user = User.objects.get(email=email)
        random_password = get_random_string(6)
        user.set_password(random_password)
        user.save()

        from django.core import mail

        emails = (
            ('Reset Password', 'This is new password:'+random_password, 'admin@gmail.com', [email]),
        )
        results = mail.send_mass_mail(emails)
        response_data['email'] = email
#        response_data['num_results'] = len(results)

    except User.DoesNotExist:
        response_data[ERROR_CODE] = WRONG_EMAIL
        response_data[ERROR_MESSAGE] = WRONG_EMAIL_MESSAGE
    return  json_http(response_data)

@login_require
@user_id_require
def get_user_detail(request):
    user_id = request.POST.get(USER_ID)
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        user = User.objects.get(pk=user_id)
        if not user.is_active:
            response_data[ERROR_CODE] = USER_BLOCKED
            response_data[ERROR_MESSAGE] = USER_BLOCKED_MESSAGE
            return  json_http(response_data)

        response_data[USER_ID] = user.id
        response_data[FIRST_NAME] = user.first_name
        response_data[LAST_NAME] = user.last_name
        response_data[PHOTO] = unicode(user.photo) if '://' in unicode(user.photo) else settings.MEDIA_URL + unicode(user.photo)
        response_data[NUM_FOLLOWER] = user.num_follower
        response_data[NUM_LIKE] = user.num_like
        response_data[NUM_PHOTO] = user.num_photo
        response_data[NUM_EVENT] = user.num_event
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

@login_require
@require_http_post
def upload_user_photo(request):
    photo = request.FILES.get(PHOTO, '')
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        user = request.user
        photo_url = save_file(file=photo, upload_to='user')
        user.photo = photo_url
        response_data[PHOTO] = settings.MEDIA_URL+photo_url
        user.save()
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

@login_require
@friend_id_require
@require_http_post
def set_follow_user(request):
    followed = request.POST.get(FOLLOWED)
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        friend = request.friend
        user = request.user
        try:
            user_friend = UserFriend.objects.get(user_id=user.id, friend_id=friend.id)
            if followed == '0':
                user_friend.delete()
                friend.num_follower -= 1
        except UserFriend.DoesNotExist:
            UserFriend.objects.create(user_id=user.id, friend_id=friend.id)
            friend.num_follower += 1
        friend.save()
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

@login_require
@require_http_post
def get_list_owner_followers(request):
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        user = request.user
        userfriendfilters = UserFriend.objects.filter(friend_id=user.id)
        user_list = []
        for userfriendfilter in userfriendfilters:
            user_item = {}
            user_item[USER_ID] = userfriendfilter.friend.id
            user_item[FIRST_NAME] = userfriendfilter.friend.first_name
            user_item[LAST_NAME] = userfriendfilter.friend.last_name
            user_item[PHOTO] = unicode(userfriendfilter.friend.photo) if '://' in unicode(userfriendfilter.friend.photo) else settings.MEDIA_URL + unicode(userfriendfilter.friend.photo)
            user_item[NUM_FOLLOWER] = userfriendfilter.friend.num_follower
            user_item[NUM_LIKE] = userfriendfilter.friend.num_like
            user_item[NUM_PHOTO] = userfriendfilter.friend.num_photo
            user_list.append(user_item)
        response_data['users'] = user_list
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

@login_require
@require_http_post
@user_id_require
def get_list_user_followers(request):
    response_data = {ERROR_CODE:NO_ERROR}
    user_id = request.POST.get(USER_ID, '')
    try:
        userfriendfilters = UserFriend.objects.filter(friend_id=user_id)
        user_list = []
        for userfriendfilter in userfriendfilters:
            user_item = {}
            user_item[USER_ID] = userfriendfilter.friend.id
            user_item[FIRST_NAME] = userfriendfilter.friend.first_name
            user_item[LAST_NAME] = userfriendfilter.friend.last_name
            user_item[PHOTO] = unicode(userfriendfilter.friend.photo) if '://' in unicode(userfriendfilter.friend.photo) else settings.MEDIA_URL + unicode(userfriendfilter.friend.photo)
            user_item[NUM_FOLLOWER] = userfriendfilter.friend.num_follower
            user_item[NUM_LIKE] = userfriendfilter.friend.num_like
            user_item[NUM_PHOTO] = userfriendfilter.friend.num_photo
            user_list.append(user_item)
        response_data['users'] = user_list
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

@user_id_require
@login_require
@require_http_post
def set_abused_reports(request):
    to = request.POST.get(TO, '') or 'tamirkeren1@gmail.com'
    cc = request.POST.get(CC, '')
    bcc = request.POST.get(BCC, '')
    content = request.POST.get(CONTENT, '')
    if not content:
        return json_http(None)
    abused_user_id = request.POST.get(USER_ID, '')

    response_data = {ERROR_CODE:NO_ERROR}
    try:
        abused_user = User.objects.get(pk=abused_user_id)
        report, created = AbuseReport.objects.get_or_create(user_id = abused_user_id, reporter_id = request.user.id)
        report.to = to
        report.cc = cc
        report.bcc = bcc
        report.content = content
        report.user = abused_user
        report.reporter = request.user

        if created:
            abused_user.num_reports+=1
            if abused_user.num_reports > 1 and abused_user.num_reports <=5:
                abused_user.level = LOWER
            elif abused_user.num_reports > 5 and abused_user.num_reports <=10:
                abused_user.level = MIDDLE
            elif abused_user.num_reports > 10:
                abused_user.level = HIGH
            abused_user.save()
        report.save()

        response_data[REPORT_ID] = report.id
        response_data[TO] = report.to
        response_data[CC] = report.cc
        response_data[BCC] = report.bcc
        response_data[CONTENT] = report.content
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return json_http(response_data)