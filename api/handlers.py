from piston.handler import BaseHandler
from releases.models import Release


class ReleaseHandler(BaseHandler):
    allowed_methods = ('GET',)
    model = Release
    
    def read(self, request):

        base = Release.objects
        if request.GET.has_key('url'):
            return base.get(url=request.GET['url'])

        base = base.all().order_by('-date')

        if request.GET.has_key('source_id'):
            base = base.filter(source=request.GET['source_id'])
        if request.GET.has_key('source_name'):
            base = base.filter(source__organization__icontains=request.GET['source_name'])
        if request.GET.has_key('source_type'):
            base = base.filter(source__source_type=request.GET['source_type'])             

        return base[:10]
