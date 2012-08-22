import sys
import logging
from traceback import format_tb
from django.core.management.base import BaseCommand, CommandError
from releases.models import Release
from sources.models import Source, SourceScrapeFailure
from readability.readability import Document
from lxml import html
import datetime
from util import condense_whitespace
import dateutil.parser
import requests
import superfastmatch
from now import now
from superfastmatch.djangoclient import from_django_conf
from django.conf import settings


control_characters = dict.fromkeys(range(32))
control_characters['\t'] = '\t'
control_characters['\n'] = '\n'
control_characters['\r'] = '\r'
control_characters[127] = None
def kill_control_characters(s):
    return s.translate(control_characters)

def get_link_content(link):
    content = requests.get(link).content
    readable = Document(content)
    body = html.fromstring(readable.summary()).text_content()
    return kill_control_characters(condense_whitespace(body))

def safely_format_traceback((exc_type, exc_value, exc_traceback)):
    try:
        return format_tb(exc_traceback)
    finally:
        del exc_type
        del exc_value
        del exc_traceback

class Command(BaseCommand):
    args = ''
    help = "Scrapes rss feeds in database for releases"

    def scrape_releases(self, source):
        feed = source.fetch_feed()

        for entry in feed['entries']:
            link = entry.get('link')
            if link.lower()[-4:] == ".pdf":
                logging.warn("Skipping PDF link: {0}".format(link))
                continue

            title = entry.get('title')
            date = dateutil.parser.parse(entry.get('published') or
                                         entry.get('updated') or
                                         entry.get('a10:updated') or
                                         now())
            body = get_link_content(link)

            try:
                # Does not use get_or_create because the unique constraint is just the url
                # and we don't want the source foreign key field to ever be null.
                release = Release.objects.get(url=link)
                release.title = title
                release.date = date
                release.body = body
                release.source = source
                release.save()
            except Release.DoesNotExist:
                release = Release.objects.create(url=link,
                                                 source=source,
                                                 title=title,
                                                 date=date,
                                                 body=body)

    def handle(self, *args, **kwargs):
        if not hasattr(settings, 'SUPERFASTMATCH'):
            raise CommandError('You must configure SUPERFASTMATCH in your project settings.')

        if not hasattr(settings, 'DEFAULT_DOCTYPE'):
            raise CommandError('You must specify a DEFAULT_DOCTYPE in your project settings.')

        self.sfm = from_django_conf()

        sources = Source.objects.filter(source_type=2)
        if len(args) == 1:
            arg = args[0]
            if arg.startswith('http://') or arg.startswith('https://'):
                sources = sources.filter(url=arg)
            else:
                try:
                    sources = sources.filter(id=int(arg))
                except ValueError:
                    raise CommandError("Arguments must be source IDs or feed URLs")

        for source in sources:
            try:
                if source.is_stale():
                    self.scrape_releases(source)
                    source.last_retrieved = now()
                    source.last_failure = None
                    source.save()

            except SourceScrapeFailure as failure:
                failure.save()

            except Exception as e:
                formatted_traceback = safely_format_traceback(sys.exc_info())
                failure = SourceScrapeFailure.objects.create(source=source,
                                                             traceback=formatted_traceback,
                                                             description=unicode(e))


