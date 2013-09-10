# -*- coding: utf-8 -*-

import sys
import logging
from traceback import print_exc
from django.core.management.base import BaseCommand, CommandError
from releases.models import Release
from sources.models import Source, SourceScrapeFailure
from readability.readability import Document
from lxml import html
from optparse import make_option
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import datetime
import dateutil.parser
import requests
import superfastmatch
from util import readability_extract, kill_control_characters
from now import now
from releases.scrape import scrape_release
from superfastmatch.djangoclient import from_django_conf
from django.conf import settings


class Command(BaseCommand):
    args = ''
    help = "Scrapes rss feeds in database for releases"
    option_list = BaseCommand.option_list + (
        make_option('--including-stale',
                    action='store_true',
                    dest='including_stale',
                    default=False,
                    help='Don\'t skip recently-retrieved sources.'),
    )

    def scrape_releases(self, source):
        feed = source.fetch_feed()

        for entry in feed['entries']:
            link = entry.get('link')
            if link.lower()[-4:] == ".pdf":
                logging.warn("Skipping PDF link: {0}".format(link))
                continue

            scrape_release(source, feed, entry, link)


    def handle(self, *args, **options):
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
                if source.is_stale() or options['including_stale']:
                    self.scrape_releases(source)
                    source.last_retrieved = now()
                    source.last_failure = None
                    source.save()

            except SourceScrapeFailure as failure:
                failure.save()

            except Exception as e:
                buf = StringIO()
                print_exc(1000, buf)
                failure = SourceScrapeFailure.objects.create(source=source,
                                                             traceback=buf.getvalue(),
                                                             description=unicode(e))


