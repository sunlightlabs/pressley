from django.core.management.base import BaseCommand, CommandError
from releases.models import Release
from sources.models import Source
import superfastmatch
from settings import SUPERFASTMATCH

class Command(BaseCommand):
    args = '<none>'
    help = "Posts press releases in pressley to sfm"

    def handle(self, *args, **kwargs):

        sfm = superfastmatch.Client(url=SUPERFASTMATCH['default']['url'])
        releases = Release.objects.all()
        for r in releases:
            response = sfm.add(r.source.doc_type or SUPERFASTMATCH['default']['doctype'], r.id, r.body, title=r.title, date=r.date, source=r.source.organization)
            print response
    
