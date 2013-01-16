from django.db import models
from gauth.models import User

class Event(models.Model):
    title = models.CharField(max_length=299)
    time_limit = models.FloatField(default=24)
    num_member = models.IntegerField('Number of members', default=1)
    num_likes = models.IntegerField('Number of likes',default=0)
    num_images = models.IntegerField('Number of images',default=0)
    num_comments = models.IntegerField('Number of comments',default=0)
    phone = models.CharField(max_length=15, null=True, blank=True)
    created_date = models.DateTimeField(auto_now=True)
    modified_date = models.DateTimeField(auto_now_add=True)
    code = models.CharField(blank=True, null=True, max_length=100)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='created_user+')
    is_public = models.BooleanField('public',default=True)
    is_active = models.BooleanField('active',default=True)
    posted = models.BooleanField(default=False)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    place_address = models.CharField(max_length=300, null=True, blank=True)
    place_name = models.CharField(max_length=300, null=True, blank=True)
    
    users = models.ManyToManyField(User, related_name='user+', through='EventUser')
    
    def __unicode__(self):
        return self.title

    def address(self):
        return "%s %s"%(self.place_address, self.place_name)
    
class EventUser(models.Model):
    event = models.ForeignKey(Event, related_name='event+')
    user = models.ForeignKey(User, related_name='user+')
    joining = models.BooleanField(default=False)
    joined = models.BooleanField(default=False)
    liked = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)

class Image(models.Model):
    source = models.ImageField(upload_to='events')
    num_likes = models.IntegerField(default=0)
    num_comments = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, related_name='user+')
    event = models.ForeignKey(Event, related_name='event+')

class Image_Like(models.Model):
    image = models.ForeignKey(Image, related_name='image+')
    user = models.ForeignKey(User, related_name='user+')
    vote = models.BooleanField(default=True)

class AbuseReport(models.Model):
    to = models.EmailField(max_length=200)
    cc = models.CharField(max_length=1000)
    bcc = models.CharField(max_length=1000)
    subject = models.CharField(max_length=1000)
    user = models.ForeignKey(User, related_name='user+')
    reporter = models.ForeignKey(User, related_name='reporter+')
    event = models.ForeignKey(Event, related_name='event+')
    content = models.TextField()
    created_date = models.DateTimeField(auto_now=True)