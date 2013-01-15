from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from gauth.views import register, login, login_via_facebook, forgot_password, get_user_detail,\
     upload_user_photo, set_follow_user, get_list_owner_followers, get_list_user_followers

from gevents.views import get_live_events, get_event_detail, get_photo_detail, vote_photo,\
     get_join_user_list, set_status_event, join_event, leave_event, create_event, edit_event, upload_event_image,\
     get_list_own_events, get_list_user_events, delete_image, get_own_photos, get_user_photos,\
     get_joinable_events, get_posted_events, set_posted_event, get_unpublished_events, set_abused_reports
from gcomments.views import comment
from testform.views import test

# Uncomment the next two lines to enable the admin:
import gadmin
gadmin.autodiscover()

urlpatterns = patterns('',
    url(r'^test$', test, name='test'),
    url(r'^api/user/login$', login, name='login'),
    url(r'^api/user/register$', register, name='register'),
    url(r'^api/user/login_via_facebook$', login_via_facebook, name='login_via_facebook'),
    url(r'^api/user/forgot_password$', forgot_password, name='forgot_password'),
    url(r'^api/user/get_user_detail$', get_user_detail, name='get_user_detail'),
    url(r'^api/user/upload_user_photo$', upload_user_photo, name='upload_user_photo'),
    url(r'^api/user/set_follow_user$', set_follow_user, name='set_follow_user'),
    url(r'^api/user/get_list_owner_followers$', get_list_owner_followers, name='get_list_owner_followers'),
    url(r'^api/user/get_list_user_followers$', get_list_user_followers, name='get_list_user_followers'),


    url(r'^api/event/get_live_events$', get_live_events, name='get_live_events'),
    url(r'^api/event/set_posted_event$', set_posted_event, name='set_posted_event'),
    url(r'^api/event/get_posted_events$', get_posted_events, name='get_posted_events'),
    url(r'^api/event/get_unpublished_events$', get_unpublished_events, name='get_unpublished_events'),
    url(r'^api/event/get_joinable_events$', get_joinable_events, name='get_joinable_events'),
    url(r'^api/event/get_event_detail$', get_event_detail, name='get_event_detail'),
    url(r'^api/event/get_photo_detail$', get_photo_detail, name='get_photo_detail'),
    url(r'^api/event/vote_photo$', vote_photo, name='vote_photo'),
    url(r'^api/event/get_join_user_list$', get_join_user_list, name='get_join_user_list'),
    url(r'^api/event/set_status_event$', set_status_event, name='set_status_event'),
    url(r'^api/event/join_event$', join_event, name='join_event'),
    url(r'^api/event/leave_event$', leave_event, name='leave_event'),
    url(r'^api/event/create_event$', create_event, name='create_event'),
    url(r'^api/event/edit_event$', edit_event, name='edit_event'),
    url(r'^api/event/upload_event_image$', upload_event_image, name='upload_event_image'),
    url(r'^api/event/get_list_own_events$', get_list_own_events, name='get_list_own_events'),
    url(r'^api/event/get_list_user_events$', get_list_user_events, name='get_list_user_events'),
    url(r'^api/event/delete_image$', delete_image, name='delete_image'),
    url(r'^api/event/get_own_photos$', get_own_photos, name='get_own_photos'),
    url(r'^api/event/get_user_photos$', get_user_photos, name='get_user_photos'),
    url(r'^api/event/set_abused_reports$', set_abused_reports, name='set_abused_reports'),

    url(r'^api/image/comment$', comment, name='comment'),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(gadmin.site.urls)),
)

if settings.DEBUG:
    # add one of these for every non-static root you want to serve
    urlpatterns+= static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # this take cares of static media (i.e. bundled in apps, and specified in settings)
    urlpatterns+= staticfiles_urlpatterns()
