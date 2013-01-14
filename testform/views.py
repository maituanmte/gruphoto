# Create your views here.
from django.views.generic.simple import direct_to_template
def test(request):
    return direct_to_template(request, template="test.html")
