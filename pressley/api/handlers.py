from piston.handler import BaseHandler
from releases.models import Release


class ReleaseHandler(BaseHandler):
    allowed_methods = ('GET',)
    model = Release
    
    def read(self, request, release_id=None):
        
        base = Release.objects
        if release_id:
            return base.get(id=release_id)
        else:
            return base.all()[:10] 
