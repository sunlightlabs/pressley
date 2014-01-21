import logging
from django.core.management.base import BaseCommand, CommandError
from releases.models import Release
from sources.models import Source, SourceScrapeFailure
from releases.scraping import get_link_content
import datetime
import dateutil.parser
import superfastmatch
from now import now
from superfastmatch.djangoclient import from_django_conf
from django.conf import settings


class Command(BaseCommand):
    args = '<none>'
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
            source_name = source.organization
            (_trash_title, body) = get_link_content(link)

            (release, created) = Release.objects.get_or_create(url=link,
                                                               title=title,
                                                               date=date,
                                                               body=body,
                                                               source=source)
            if body is None or len(body.strip()) == 0:
                continue

            try:
                result = self.sfm.add(doctype=source.doc_type or settings.DEFAULT_DOCTYPE,
                                      docid=release.id,
                                      text=body,
                                      defer=True,
                                      source=source_name,
                                      date=date,
                                      title=title,
                                      put=False)
            except superfastmatch.SuperFastMatchError as e:
                raise SourceScrapeFailure(source=source, description=unicode(e))

            if result['success'] != True:
                msg = 'Superfastmatch failure: {0}'.format(result.get('error', ''))
                raise SourceScrapeFailure(source,
                                          description=msg)


    def handle(self, *args, **kwargs):
        if not hasattr(settings, 'SUPERFASTMATCH'):
            raise CommandError('You must configure SUPERFASTMATCH in your project settings.')

        if not hasattr(settings, 'DEFAULT_DOCTYPE'):
            raise CommandError('You must specify a DEFAULT_DOCTYPE in your project settings.')

        self.sfm = from_django_conf()

        sources = Source.objects.filter(source_type=2)

        for source in sources:
            try:
                if source.is_stale():
                    self.scrape_releases(source)
                    source.last_retrieved = now()
                    source.save()

                    failures = SourceScrapeFailure.objects.filter(resolved__isnull=True,
                                                                  source=source)
                    for f in failures:
                        f.resolved = now()
                        f.save()

            except SourceScrapeFailure as failure:
                failure.save()

            except Exception as e:
                failure = SourceScrapeFailure.objects.create(source=source,
                                                             description=unicode(e))


