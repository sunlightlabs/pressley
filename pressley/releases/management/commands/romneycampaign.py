# -*- coding: utf-8 -*-

import re
import logging

from traceback import print_exc
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import lxml.html
import requests
import dateutil.parser

from optparse import make_option
from django.core.management import BaseCommand, CommandError

from util import kill_control_characters, readability_extract
from sources.models import Source, SourceScrapeFailure
from releases.models import Release


IndexUrl = 'http://www.mittromney.com/news/press-releases'
Organization = 'Romney for President, Inc.'
DocType = 7

class RomneyRelease(object):
    def __init__(self, title, url, date):
        self.title = title
        self.url = url
        self.date = date
        self._body = None

    @property
    def body(self):
        if self._body is None:
            response = requests.get(self.url)
            response.raise_for_status()
            (_junk_title, body) = readability_extract(response.content)
            self._body = kill_control_characters(body)
        return self._body


class RomneyReleaseIndexPage(object):
    def __init__(self, page_number=0):
        response = requests.get(IndexUrl, params={'page': page_number})
        response.raise_for_status()
        document = lxml.html.fromstring(response.content)
        document.make_links_absolute(IndexUrl)

        self.page_number = page_number
        self.row_elements = document.xpath("//div[@class='inner content']/div[@class='view-content']/div[contains(@class, 'views-row')]")
        self.current_index = len(self.row_elements) - 1

    def __iter__(self):
        return self

    def next(self):
        if self.current_index < 0:
            raise StopIteration

        elem = self.row_elements[self.current_index]
        self.current_index -= 1
        (title_elem, a_elem, date_elem) = [e
                                           for e in elem.iterdescendants()
                                           if e.tag in ('span', 'a')]
        url = a_elem.attrib['href']
        date = dateutil.parser.parse(date_elem.text_content())
        return RomneyRelease(title_elem.text_content(),
                             url,
                             date.date())

class RomneyReleaseIterator(object):
    def __init__(self):
        response = requests.get(IndexUrl)
        response.raise_for_status()
        document = lxml.html.fromstring(response.content)
        pager_text = ''.join(document.xpath('//*[@id="view-id-press_releases_hack-page_1"]//li[contains(@class, "pager-total")]/text()'))
        match = re.compile(ur'of (\d+)').match(pager_text)
        if match is None:
            raise CommandError("Failed to find the pagination control.")
        last_page_index = int(match.group(1)) - 1
        self.current_page = RomneyReleaseIndexPage(last_page_index)

    def __iter__(self):
        return self

    def next(self):
        try:
            return self.current_page.next()
        except StopIteration:
            if self.current_page.page_number == 0:
                raise
            else:
                self.current_page = RomneyReleaseIndexPage(self.current_page.page_number - 1)
                return self.current_page.next()

class Command(BaseCommand):
    args = '<none>'
    help = "Scrapes press releases for the Romney for President campaign."
    option_list = BaseCommand.option_list + (
        make_option('--all',
                    action='store_true',
                    dest='all',
                    default=False,
                    help='Scrape all releases, rather than resuming base on the latest scraped release.'),
        make_option('--loglevel',
                    action='store',
                    choices=['debug', 'info', 'warning', 'error', 'critical'],
                    default='warning',
                    help='Logging level'),
    )

    def handle(self, *args, **options):
        logging.basicConfig(level=getattr(logging, options['loglevel'].upper()))
        logging.getLogger('requests.packages.urllib3.connectionpool').level = getattr(logging, options['loglevel'].upper())

        (source, created) = Source.objects.get_or_create(organization=Organization,
                                                         url=IndexUrl,
                                                         doc_type=DocType,
                                                         source_type=3)

        scraped_releases = Release.objects.filter(source=source)
        if options['all'] or scraped_releases.count() == 0:
            releases = RomneyReleaseIterator()
        else:
            last_scraped_release = scraped_releases.order_by('-created')[0]
            releases = RomneyReleaseIterator()
            logging.info("Most recent release: {rel.date} {rel.url}".format(rel=last_scraped_release))
            logging.info("Fast-forwarding.")
            for rel in releases:
                if rel.url == last_scraped_release.url:
                    break 
                else:
                    logging.debug("Skipping {rel.url}".format(rel=rel))

        try:
            for r in releases:
                (release, created) = Release.objects.get_or_create(
                    source=source,
                    date=r.date,
                    url=r.url,
                    title=r.title,
                    body=r.body)
                if created:
                    logging.notice("Scraped {rel.url)".format(rel=r))

        except Exception as e:
            buf = StringIO()
            print_exc(1000, buf)
            raise SourceScrapeFailure.objects.create(source=source,
                                                     traceback=buf.getvalue(),
                                                     description=unicode(e))

