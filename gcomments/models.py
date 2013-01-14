from django.db import models
from gauth.models import User
from gevents.models import Image

NO_PARENT = 0

class Comment(models.Model):
    content = models.TextField()
    created_date = models.DateTimeField(auto_now=True)
    parent = models.IntegerField(default=NO_PARENT)
    user = models.ForeignKey(User, related_name='user+')
    image = models.ForeignKey(Image, related_name='image+')
    num_reply = models.IntegerField(default=0)

