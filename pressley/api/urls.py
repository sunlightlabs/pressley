from django.conf.urls.defaults import *
from piston.resource import Resource
from api.handlers import ReleaseHandler

release_handler = Resource(ReleaseHandler)

urlpatterns = patterns('', 
    url(r'^releases(\.(?P<emitter_format>.+))$', release_handler),
 )
