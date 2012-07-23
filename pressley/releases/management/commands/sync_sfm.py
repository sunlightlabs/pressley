from django.core.management.base import BaseCommand, CommandError
from releases.models import Release
from sources.models import Source
import superfastmatch
from settings import SUPERFASTMATCH

class Command(BaseCommand):
    args = '<none>'
    help = "Posts press releases in pressley to sfm"

    def handle(self, *args, **kwargs):

        servers = SUPERFASTMATCH['default']
        post_servers = []
        for s in servers:
            sfm = superfastmatch.Client(url=s['url'])
            post_servers.append((sfm, s['doctype']))

        
        releases = Release.objects.all()
        for r in releases:
            for ps in post_servers:
                try:
                    response = ps[0].add(r.source.doc_type or ps[1], r.id, r.body, title=r.title, date=r.date, source=r.source.organization)
                    print response
                except superfastmatch.SuperFastMatchError as e:
                    print "could not add document %s with doctype %s to sfm" % (r.id, r.source.doc_type)

    
