from django.contrib.admin.widgets import AdminFileWidget
from django import forms
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.conf import settings
from django.contrib.admin.templatetags.admin_static import static
from PIL import Image
import os

try:
    from sorl.thumbnail.main import DjangoThumbnail
    def thumbnail(image_path):
        t = DjangoThumbnail(relative_source=image_path, requested_size=(200,200))
        return u'<img id="image_view" height="150" width="122" src="%s" alt="%s" />' % (t.absolute_url, image_path)
except ImportError:
    def thumbnail(image_path):
        absolute_url = os.path.join(settings.MEDIA_URL, image_path)
        return u'<img id="image_view" height="150" width="122" src="%s" alt="%s" />' % (absolute_url, image_path)

class AdminImageWidget(AdminFileWidget):
    """
    A FileField Widget that displays an image instead of a file path
    if the current file is an image.
    """
    
    template_with_initial = ('')
    template_with_clear = ('')
    
    @property
    def media(self):
        js = ["qquploader.js",]
        return forms.Media(js=[static("admin/js/%s" % path) for path in js])
    
    def render(self, name, value, attrs=None):
        output = []
        file_name = str(value)
        if file_name:
            file_path = '%s%s' % (settings.MEDIA_URL, file_name)
            try:            # is image
                Image.open(os.path.join(settings.MEDIA_ROOT, file_name))
                output.append('<a id="id_photo_link" target="_blank" href="%s">%s</a><br />' % \
                    (file_path, thumbnail(file_name)))
            except IOError: # not image
                output.append('<a id="id_photo_link" target="_blank" href="%s">%s</a><br />' %\
                              ('/media/user/default-avatar.png', thumbnail('user/default-avatar.png')))
            
        output.append(super(AdminImageWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))
