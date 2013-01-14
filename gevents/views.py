from gevents.models import Event, Image, EventUser, Image_Like
from gauth.models import User, UserFriend
from gcomments.models import Comment
from math import radians, cos, sin, asin, sqrt, degrees, acos, atan2
from django.conf import settings
from grouphoto import save_file
from datetime import datetime
from grouphoto import json_http
import socket, ssl, json, struct

from grouphoto.errors import NO_ERROR, UNKNOWN_ERROR, UNKNOWN_ERROR_MESSAGE, ERROR_CODE, ERROR_MESSAGE, \
    EVENT_CODE_NOT_SET, EVENT_CODE_NOT_SET_MESSAGE, \
    NO_PERMISSION, NO_PERMISSION_MESSAGE,\
    EVENT_BLOCKED, EVENT_BLOCKED_MESSAGE, \
    EVENT_BLOCKED_USER, EVENT_BLOCKED_USER_MESSAGE
from grouphoto.fields import FIRST_NAME, LAST_NAME, PHONE, PHOTO, NUM_FOLLOWER,\
    NUM_LIKE, NUM_PHOTO, USER_ID, NUM_MEMBER, LONGITUDE, LATITUDE, DISTANCE, \
    PLACE_ADDRESS, TIME_LIMIT, EVENT_ID, TITLE, NAME, DESCRIPTION, PLACE_NAME, CREATED_DATE, IMAGE_ID,\
    IS_PUBLIC, SOURCE, CODE, CONTENT, VOTE, NUM_COMMENT, NUM_EVENT
from grouphoto.decorator import require_http_post, login_require, event_id_require, image_id_require, user_id_require


@login_require
@require_http_post
def get_live_events(request):
    events = Event.objects.all()
    response_data = {ERROR_CODE:NO_ERROR}
    event_list = []
    try:
        original_time = datetime(2013, 1, 1, 0,0,0)
        end_time = (datetime.now() - original_time).total_seconds()
        end_time_minute = end_time/60
        for event in events:
            created = event.created_date
            time = datetime(created.year, created.month, created.day, created.hour, created.minute, created.second)
            start_time = (time - original_time).total_seconds()
            start_time_minute = start_time/60
            result = end_time_minute - start_time_minute
            time_limit = event.time_limit * 60
            if result < time_limit:
                event_item = {}
                user_data = {}
                user = event.created_by
                user_data[USER_ID] = user.id
                user_data[NAME] = user.full_name()
                user_data[PHOTO] = settings.MEDIA_URL+unicode(user.photo)

                event_item[EVENT_ID] = event.id
                event_item[TITLE] = event.title
                event_item[NUM_MEMBER] = event.num_member
                event_item[NUM_LIKE] = event.num_likes
                event_item[NUM_PHOTO] = event.num_images
                event_item[LONGITUDE] = event.longitude
                event_item[LATITUDE] = event.latitude
                event_item[PLACE_ADDRESS] = event.place_address
                event_item[TIME_LIMIT] = time_limit

                event_list.append(event_item)

        response_data['events'] = event_list
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return json_http(response_data)

def haversine(long_a, lat_a, long_b, lat_b):
    R = 6371
    lon1 = radians(long_a)
    lat1 = radians(lat_a)
    lon2 = radians(long_b)
    lat2 = radians(lat_b)
    x = (lon2-lon1) * cos((lat1+lat2)/2)
    y = (lat2-lat1);
    d = sqrt(x*x + y*y) * R
    return d * 1000 #convert to metter

@login_require
@require_http_post
def get_joinable_events(request):
    latitude = request.POST.get(LATITUDE, '')
    longitude = request.POST.get(LONGITUDE, '')
    distance = request.POST.get(DISTANCE, '') or 100
    if not latitude or not longitude or not distance:
        return json_http(None)
    events = Event.objects.all()

    response_data = {}
#    try:
    event_list = []
    original_time = datetime(2013, 1, 1, 0,0,0)
    end_time = (datetime.now() - original_time).total_seconds()
    end_time_minute = end_time/60
    for event in events:
        created = event.created_date
        time = datetime(created.year, created.month, created.day, created.hour, created.minute, created.second)
        start_time = (time - original_time).total_seconds()
        start_time_minute = start_time/60
        result = end_time_minute - start_time_minute
        time_limit = event.time_limit * 60

        current_distance = haversine(float(longitude), float(latitude), float(event.longitude), float(event.latitude))
        if current_distance <= float(distance) and result < time_limit:
            event_item = {}
            user_data = {}
            user = event.created_by
            user_data[USER_ID] = user.id
            user_data[NAME] = user.full_name()
            user_data[PHOTO] = unicode(user.photo) if '://' in unicode(user.photo) else settings.MEDIA_URL + unicode(user.photo)

            event_item[EVENT_ID] = event.id
            event_item[TITLE] = event.title
            event_item[NUM_MEMBER] = event.num_member
            event_item[NUM_LIKE] = event.num_likes
            event_item[NUM_PHOTO] = event.num_images
            event_item[LONGITUDE] = event.longitude
            event_item[LATITUDE] = event.latitude
            event_item[PLACE_ADDRESS] = event.place_address
            event_item[TIME_LIMIT] = event.time_limit*60
            event_item['current_distance'] = current_distance

            event_list.append(event_item)
    response_data['events'] = event_list
#    except:
#        response_data[ERROR_CODE] = UNKNOWN_ERROR
#        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return json_http(response_data)


@require_http_post
@login_require
@event_id_require
def get_event_detail(request):
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        event = request.event

        response_data[EVENT_ID] = event.id
        response_data[CREATED_DATE] = unicode(event.created_date)
        response_data[TITLE] = event.title
        response_data[NUM_LIKE] = event.num_likes
        response_data[NUM_PHOTO] = event.num_images
        response_data[NUM_MEMBER] = event.num_member

        image_list = []
        images = Image.objects.filter(event=event.id)
        for image in images:
            image_item = {}
            owner = image.owner
            creator = {USER_ID:owner.id, NAME:owner.full_name(), PHOTO:unicode(owner.photo) if '://' in unicode(owner.photo) else settings.MEDIA_URL + unicode(owner.photo)}
            comments = Comment.objects.filter(image_id=image.id)
            comments_list = []
            for comment in comments:
                comment_item = {}

                user_comment = comment.user
                user_comment_data = {}
                user_comment_data[USER_ID] = user_comment.id
                user_comment_data[NAME] = user_comment.full_name()
                user_comment_data[PHOTO] = unicode(user_comment.photo) if '://' in unicode(user_comment.photo) else settings.MEDIA_URL + unicode(user_comment.photo)
                comment_item['user'] = user_comment_data
                comment_item[CONTENT] = comment.content

                comments_list.append(comment_item)

            image_item['creator'] = creator
            image_item['comments'] = comments_list
            image_item[IMAGE_ID] = image.id
            image_item[SOURCE] = settings.MEDIA_URL+unicode(image.source)
            image_item[NUM_LIKE] = image.num_likes

            image_list.append(image_item)

        user_list = []
        event_users = EventUser.objects.filter(pk=event.id, joined=True)
        for event_user in event_users:
            user_id = event_user.user_id
            user = User.objects.get(pk=user_id)
            user_item = {}
            user_item[USER_ID] = user.id
            user_item[FIRST_NAME] = user.first_name
            user_item[LAST_NAME] = user.last_name
            user_item[NUM_LIKE] = user.num_like
            user_item[NUM_FOLLOWER] = user.num_follower
            user_item[NUM_PHOTO] = user.num_photo

            user_list.append(user_item)

        response_data['photos'] = image_list
        response_data['users'] = user_list

    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

@require_http_post
@login_require
def create_event(request):
    title = request.POST.get(TITLE,'')
    description = request.POST.get(DESCRIPTION,'')
    if not title or not description:
        return json_http(None)
    latitude = request.POST.get(LATITUDE,'') or 0
    longitude = request.POST.get(LONGITUDE,'') or 0
    place_address = request.POST.get(PLACE_ADDRESS,'')
    place_name = request.POST.get(PLACE_NAME,'')
    phone = request.POST.get(PHONE,'')
    time_limit = request.POST.get(TIME_LIMIT,'') or 24
    is_public = request.POST.get(IS_PUBLIC,'')
    code = request.POST.get(CODE,'')

    response_data = {ERROR_CODE:NO_ERROR}

    if is_public != 'on' and not code:
        response_data[ERROR_CODE] = EVENT_CODE_NOT_SET
        response_data[ERROR_MESSAGE] = EVENT_CODE_NOT_SET_MESSAGE
        return  json_http(response_data)

    try:
        user = request.user

        event = Event()
        event.created_by_id = user.id
        event.description = description
        event.latitude = latitude
        event.longitude = longitude
        event.place_address = place_address
        event.place_name = place_name
        event.phone = phone
        event.time_limit = time_limit
        event.is_public = is_public
        event.code = code
        event.title = title

        event.save()

        event_user = EventUser()
        event_user.user_id = user.id
        event_user.event_id = event.id
        event_user.joined = True
        event_user.joining = True
        event_user.save()

        user.num_event += 1
        user.save()

        response_data[EVENT_ID] = event.id
        response_data[TITLE] = event.title
        response_data[DESCRIPTION] = event.description
        response_data[LATITUDE] = event.latitude
        response_data[LONGITUDE] = event.longitude
        response_data[TIME_LIMIT] = event.time_limit
        response_data[IS_PUBLIC] = event.is_public
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE
    return  json_http(response_data)

@require_http_post
@login_require
def edit_event(request):
    title = request.POST.get(TITLE,'')
    description = request.POST.get(DESCRIPTION,'')
    if not title or not description:
        return json_http(None)

    response_data = {ERROR_CODE:NO_ERROR}

    try:
        event = request.event
        user = request.user
        if event.created_by_id != user.id:
            response_data[ERROR_CODE] = NO_PERMISSION
            response_data[ERROR_MESSAGE] = NO_PERMISSION_MESSAGE
            return  json_http(response_data)
        event.description = description
        event.title = title

        event.save()

        response_data[EVENT_ID] = event.id
        response_data[TITLE] = event.title
        response_data[DESCRIPTION] = event.description
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE
    return  json_http(response_data)


@require_http_post
@login_require
@image_id_require
def get_photo_detail(request):
    response_data = {ERROR_CODE:NO_ERROR}

    image = request.image

    owner = image.owner
    creator = {}
    creator[USER_ID] = owner.id
    creator[NAME] = owner.full_name()
    creator[PHOTO] = unicode(owner.photo) if '://' in unicode(owner.photo) else settings.MEDIA_URL + unicode(owner.photo)

    comment_list = []
    comments = Comment.objects.filter(image_id=image.id)
    for comment in comments:
        comment_item = {}

        user = comment.user
        user_comment = {}
        user_comment[USER_ID] = user.id
        user_comment[NAME] = user.full_name()
        user_comment[PHOTO] = unicode(user.photo) if '://' in unicode(user.photo) else settings.MEDIA_URL + unicode(user.photo)

        comment_item[CONTENT] = comment.content
        comment_item['user'] = user_comment

        comment_list.append(comment_item)

    response_data[IMAGE_ID] = image.id
    response_data[SOURCE] = settings.MEDIA_URL+unicode(image.source)
    response_data[NUM_LIKE] = image.num_likes
    response_data[NUM_COMMENT] = image.num_comments
    response_data['creator'] = creator
    response_data['comments'] = comment_list

    return  json_http(response_data)

@require_http_post
@login_require
@image_id_require
def vote_photo(request):
    vote = request.POST.get(VOTE, '')

    response_data = {ERROR_CODE:NO_ERROR}
    try:
        image = request.image
        user = request.user
        image_like, created = Image_Like.objects.get_or_create(image_id=image.id, user_id=user.id)

        if vote == 'on':
            image_like.vote = True
            if image.num_likes == 0:
                image.event.num_likes+=1
                image.event.save()
                image.owner.num_like+=1
                image.owner.save()
            image.num_likes += 1
        else:
            if image.num_likes == 1:
                image.event.num_likes-=1
                image.event.save()
                image.owner.num_like-=1
                image.owner.save()
            image_like.vote = False
            image.num_likes -= 1
        image_like.save()
        image.save()
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

@login_require
@require_http_post
@event_id_require
def get_join_user_list(request):
    response_data = {ERROR_CODE:NO_ERROR}
    user_list = []
    try:
        event = request.event
        event_users = EventUser.objects.filter(event_id=event.id, joined=True)
        for event_user in event_users:
            user = event_user.user
            user_item = {}
            user_item[USER_ID] = user.id
            user_item[FIRST_NAME] = user.first_name
            user_item[LAST_NAME] = user.last_name
            user_item[PHOTO] = unicode(user.photo) if '://' in unicode(user.photo) else settings.MEDIA_URL + unicode(user.photo)
            user_item[NUM_FOLLOWER] = user.num_follower
            user_item[NUM_LIKE] = user.num_like
            user_item[NUM_PHOTO] = user.num_photo

            user_list.append(user_item)

        response_data['users'] = user_list

    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

def notification(device_token, message):
    thePayLoad = {
        'aps': {
            'alert':message,
            'sound':'k1DiveAlarm.caf',
            'badge':42,
            },
#        'test_data': { 'foo': 'bar' },
        }
    theCertfile = 'cert.pem'
    theHost = ( 'gateway.sandbox.push.apple.com', 2195 )
    data = json.dumps( thePayLoad )
    byteToken = bytes.fromhex(device_token)
    theFormat = '!BH32sH%ds' % len(data)
    theNotification = struct.pack( theFormat, 0, 32, byteToken, len(data), data )
    ssl_sock = ssl.wrap_socket( socket.socket( socket.AF_INET, socket.SOCK_STREAM ), certfile = theCertfile )
    ssl_sock.connect( theHost )
    ssl_sock.write( theNotification )
    ssl_sock.close()

@event_id_require
@login_require
@require_http_post
def leave_event(request):
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        event = request.event
        user = request.user
        event_user, created = EventUser.objects.get_or_create(event_id=event.id, user_id=user.id)
        event_user.joining = False
        event_user.save()

        #check neu la admin
        if user.id == event.created_by_id:
            joining_users = EventUser.objects.filter(joining=True, event_id=event.id)
            import json
            for joining_user in joining_users:
                notification(joining_user.user.device_token, 'Test notification admin leave')
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

@event_id_require
@login_require
@require_http_post
def join_event(request):
    response_data = {ERROR_CODE:NO_ERROR}
    code = request.POST.get(CODE,'')
    try:
        event = request.event
        user = request.user
        if not event.is_active:
            response_data[ERROR_CODE] = EVENT_BLOCKED
            response_data[ERROR_MESSAGE] = EVENT_BLOCKED_MESSAGE
            return  json_http(response_data)
        try:
            EventUser.objects.get(event=event, user=user, blocked=True)
            response_data[ERROR_CODE] = EVENT_BLOCKED_USER
            response_data[ERROR_MESSAGE] = EVENT_BLOCKED_USER_MESSAGE
            return  json_http(response_data)
        except EventUser.DoesNotExist:
            pass

        wrong_code = not code or code != event.code
        if user.id != event.created_by_id and not event.is_public and wrong_code:
            response_data[ERROR_CODE] = NO_PERMISSION
            response_data[ERROR_MESSAGE] = NO_PERMISSION_MESSAGE
            return  json_http(response_data)

        user = request.user
        event_user, created = EventUser.objects.get_or_create(event_id=event.id, user_id=user.id)
        event_user.joined = True
        event_user.joining = True
        event_user.save()
        if created:
            event.num_member += 1
            event.save()
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

def set_status_event(request):
    is_public = request.POST.get(IS_PUBLIC, '')
    code = request.POST.get(CODE, '')
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        event = request.event
        if is_public != 'on' and not code:
            response_data[ERROR_CODE] = EVENT_CODE_NOT_SET
            response_data[ERROR_MESSAGE] = EVENT_CODE_NOT_SET_MESSAGE
            return  json_http(response_data)
        if is_public == 'on':
            event.is_public = True
        else:
            event.is_public = False
            event.code = code
        event.save()
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

def get_events_by_user_id(user_id, response_data):
    events = Event.objects.filter(created_by_id=user_id)

    try:
        event_list = []
        for event in events:
            event_item = {}
            event_item[EVENT_ID] = event.id
            event_item[CREATED_DATE] = unicode(event.created_date)
            event_item[TITLE] = event.title
            event_item[NUM_LIKE] = event.num_likes
            event_item[NUM_PHOTO] = event.num_images
            event_item[NUM_MEMBER] = event.num_member

            image_list = []
            images = Image.objects.filter(event=event.id)
            for image in images:
                image_item = {}
                owner = image.owner
                creator = {USER_ID:owner.id, NAME:owner.full_name(), PHOTO:unicode(owner.photo) if '://' in unicode(owner.photo) else settings.MEDIA_URL + unicode(owner.photo)}
                comments = Comment.objects.filter(image_id=image.id)
                comments_list = []
                for comment in comments:
                    comment_item = {}

                    user_comment = comment.user
                    user_comment_data = {}
                    user_comment_data[USER_ID] = user_comment.id
                    user_comment_data[NAME] = user_comment.full_name()
                    user_comment_data[PHOTO] = unicode(user_comment.photo) if '://' in unicode(user_comment.photo) else settings.MEDIA_URL + unicode(user_comment.photo)
                    comment_item['user'] = user_comment_data
                    comment_item[CONTENT] = comment.content

                    comments_list.append(comment_item)

                image_item['creator'] = creator
                image_item['comments'] = comments_list
                image_item[IMAGE_ID] = image.id
                image_item[SOURCE] = settings.MEDIA_URL+unicode(image.source)
                image_item[NUM_LIKE] = image.num_likes

                image_list.append(image_item)

            user_list = []
            event_users = EventUser.objects.filter(event_id=event.id, joined=True)
            for event_user in event_users:
                user_id = event_user.user_id
                user = User.objects.get(pk=user_id)
                user_item = {}
                user_item[USER_ID] = user.id
                user_item[FIRST_NAME] = user.first_name
                user_item[LAST_NAME] = user.last_name
                user_item[NUM_LIKE] = user.num_like
                user_item[NUM_FOLLOWER] = user.num_follower
                user_item[NUM_PHOTO] = user.num_photo

                user_list.append(user_item)

            event_item['photos'] = image_list
            event_item['users'] = user_list
            event_list.append(event_item)
        response_data['events'] = event_list

    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE
    return response_data

@require_http_post
@login_require
def get_list_own_events(request):
    user = request.user
    response_data = {ERROR_CODE:NO_ERROR}
#    try:
    get_events_by_user_id(user.id, response_data)
#    except:
#        response_data[ERROR_CODE] = UNKNOWN_ERROR
#        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

@require_http_post
@login_require
@user_id_require
def get_list_user_events(request):
    user_id = request.POST.get(USER_ID, '')
    user = User.objects.get(pk=user_id)
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        get_events_by_user_id(user.id, response_data)
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

@event_id_require
@login_require
@require_http_post
def upload_event_image(request):
    photo = request.FILES.get(PHOTO, '')
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        event = request.event
        user = request.user
        try:
            EventUser.objects.get(event=event, user=user, joined=True)
        except EventUser.DoesNotExist:
            response_data[ERROR_CODE] = NO_PERMISSION
            response_data[ERROR_MESSAGE] = NO_PERMISSION_MESSAGE
            return  json_http(response_data)
        photo_url = save_file(file=photo, upload_to='event')
        image = Image(event_id=event.id, owner_id=user.id)
        image.source = photo_url
        image.save()
        event.num_images += 1
        event.save()
        user.num_photo += 1
        user.save()
        response_data[IMAGE_ID] = image.id
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE
    return  json_http(response_data)

@login_require
@image_id_require
@event_id_require
@require_http_post
def delete_image(request):
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        image = request.image
        user = request.user
        event = request.event
        is_admin = image.owner_id == user.id or event.created_by == user.id
        if is_admin and image.event_id == image.event_id:
            image.delete()
        else:
            response_data[ERROR_CODE] = NO_PERMISSION
            response_data[ERROR_MESSAGE] = NO_PERMISSION_MESSAGE
            return  json_http(response_data)

    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return  json_http(response_data)

@login_require
@require_http_post
def get_own_photos(request):
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        user = request.user
        images = Image.objects.filter(owner_id=user.id)
        image_list = []
        for image in images:
            image_item = {}
            image_item[IMAGE_ID] = image.id
            image_item[SOURCE] = settings.MEDIA_URL+unicode(image.source)
            image_item[NUM_LIKE] = image.num_likes
            image_item[CREATED_DATE] = unicode(image.created_date)
            image_list.append(image_item)
        response_data['photos'] = image_list
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE
    return  json_http(response_data)

@login_require
@require_http_post
@user_id_require
def get_user_photos(request):
    user_id = request.POST.get(USER_ID, '')
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        images = Image.objects.filter(owner_id=user_id)
        image_list = []
        for image in images:
            image_item = {}
            image_item[IMAGE_ID] = image.id
            image_item[SOURCE] = settings.MEDIA_URL+unicode(image.source)
            image_item[NUM_LIKE] = image.num_likes
            image_item[CREATED_DATE] = unicode(image.created_date)
            image_list.append(image_item)
        response_data['photos'] = image_list
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE
    return  json_http(response_data)

@login_require
@require_http_post
@event_id_require
def set_posted_event(request):
    event = request.event
    user = request.user
    response_data = {ERROR_CODE:NO_ERROR}
    if event.created_by_id != user.id:
        response_data[ERROR_CODE] = NO_PERMISSION
        response_data[ERROR_MESSAGE] = NO_PERMISSION_MESSAGE
        return  json_http(response_data)
    event.posted = True
    event.save()

    return  json_http(response_data)

@login_require
@require_http_post
def get_posted_events(request):
    response_data = {ERROR_CODE:NO_ERROR}
    try:
        user = request.user
        posted_events = Event.objects.filter(created_by_id=user.id, posted=True)
        event_list = []
        for event in posted_events:
            event_item = {}
            user_data = {}
            creator = event.created_by
            user_data[USER_ID] = creator.id
            user_data[NAME] = creator.full_name()
            user_data[PHOTO] = unicode(creator.photo) if '://' in unicode(creator.photo) else settings.MEDIA_URL + unicode(creator.photo)

            event_item[EVENT_ID] = event.id
            event_item[TITLE] = event.title
            event_item[NUM_MEMBER] = event.num_member
            event_item[NUM_LIKE] = event.num_likes
            event_item[NUM_PHOTO] = event.num_images
            event_item[LONGITUDE] = event.longitude
            event_item[LATITUDE] = event.latitude
            event_item[PLACE_ADDRESS] = event.place_address
            event_item[TIME_LIMIT] = event.time_limit*60

            event_list.append(event_item)

        user_friend_filters = UserFriend.objects.filter(user_id=user.id)
        for user_friend_filter in user_friend_filters:
            friend_id = user_friend_filter.friend.id

            posted_events_of_friends = Event.objects.filter(created_by_id=friend_id, posted=True)
            for event in posted_events_of_friends:
                event_item = {}
                user_data = {}
                creator = event.created_by
                user_data[USER_ID] = creator.id
                user_data[NAME] = creator.full_name()
                user_data[PHOTO] = unicode(creator.photo) if '://' in unicode(creator.photo) else settings.MEDIA_URL + unicode(creator.photo)

                event_item[EVENT_ID] = event.id
                event_item[TITLE] = event.title
                event_item[NUM_MEMBER] = event.num_member
                event_item[NUM_LIKE] = event.num_likes
                event_item[NUM_PHOTO] = event.num_images
                event_item[LONGITUDE] = event.longitude
                event_item[LATITUDE] = event.latitude
                event_item[PLACE_ADDRESS] = event.place_address
                event_item[TIME_LIMIT] = event.time_limit*60

                event_list.append(event_item)

        response_data['events'] = event_list
        response_data[NUM_EVENT] = len(event_list)
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE
    return  json_http(response_data)

@login_require
@require_http_post
def get_unpublished_events(request):
    user = request.user
    response_data = {ERROR_CODE:NO_ERROR}
    event_list = []
    try:
        events = Event.objects.filter(created_by_id=user.id)
        original_time = datetime(2013, 1, 1, 0,0,0)
        end_time = (datetime.now() - original_time).total_seconds()
        end_time_minute = end_time/60

        for event in events:
            created = event.created_date
            time = datetime(created.year, created.month, created.day, created.hour, created.minute, created.second)
            start_time = (time - original_time).total_seconds()
            start_time_minute = start_time/60
            result = end_time_minute - start_time_minute
            time_limit = event.time_limit * 60
            if result > time_limit and not event.posted:
                event_item = {}
                user_data = {}
                user = event.created_by
                user_data[USER_ID] = user.id
                user_data[NAME] = user.full_name()
                user_data[PHOTO] = settings.MEDIA_URL+unicode(user.photo)

                event_item[EVENT_ID] = event.id
                event_item[TITLE] = event.title
                event_item[NUM_MEMBER] = event.num_member
                event_item[NUM_LIKE] = event.num_likes
                event_item[NUM_PHOTO] = event.num_images
                event_item[LONGITUDE] = event.longitude
                event_item[LATITUDE] = event.latitude
                event_item[PLACE_ADDRESS] = event.place_address
                event_item[TIME_LIMIT] = time_limit
                event_item[CREATED_DATE] = unicode(event.created_date)

                event_list.append(event_item)

        response_data['events'] = event_list
    except:
        response_data[ERROR_CODE] = UNKNOWN_ERROR
        response_data[ERROR_MESSAGE] = UNKNOWN_ERROR_MESSAGE

    return json_http(response_data)