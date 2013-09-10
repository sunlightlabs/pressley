import json
import httplib
import requests
import feedparser
from pressley.now import now
from django.db import models
from django.conf import settings

class Source(models.Model):

    SOURCE_TYPE_CHOICES = (
        (1, 'rss'),
        (2, 'rss-partial'),
        (3, 'html')
    )

    source_type = models.IntegerField(choices=SOURCE_TYPE_CHOICES)
    doc_type = models.IntegerField(null=True, blank=True)
    organization = models.TextField(null=False)
    url = models.URLField(null=False, unique=True, max_length=512)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    last_retrieved = models.DateTimeField(null=True, blank=True)
    last_failure = models.OneToOneField('SourceScrapeFailure', null=True, blank=True, related_name='failed_source')

    class Meta:
        ordering = ['organization']

    def is_stale(self, seconds=None):
        seconds = seconds or settings.SCRAPE_PERIOD
        if self.last_retrieved is None:
            return True
        since_last = now() - self.last_retrieved
        if since_last.total_seconds() > seconds:
            return True
        return False

    def fetch_feed(self):
        if self.source_type not in (1, 2):
            return None

        try:
            kwargs = {}
            if self.user_agent:
                kwargs['headers'] = { 'User-Agent': self.user_agent }
            response = requests.get(self.url, **kwargs)
        except requests.exceptions.ConnectionError as e:
            raise SourceScrapeFailure.objects.create(source=self,
                                                     description=str(e))

        if response.status_code != httplib.OK:
            raise SourceScrapeFailure.objects.create(source=self,
                                                     http_status=response.status_code,
                                                     http_headers=json.dumps(response.headers),
                                                     http_body=response.text,
                                                     description="Bad HTTP response status")

        return feedparser.parse(response.text)

    def save(self, *args, **kwargs):
        super(Source, self).save(*args, **kwargs)
        if self.last_failure is None:
            failures = self.scrape_failures.filter(resolved__isnull=True)
            for f in failures:
                f.resolved = now()
                f.save()

    def is_failing(self):
        return self.scrape_failures.filter(resolved__isnull=True).count() > 0

    def __unicode__(self):
        return u"{0.organization}".format(self)

class SourceScrapeFailure(models.Model, Exception):

    source = models.ForeignKey(Source, related_name='scrape_failures')

    http_status = models.IntegerField(null=True)
    http_headers = models.TextField(null=True)
    http_body = models.TextField(null=True, blank=True)

    traceback = models.TextField(null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    resolved = models.DateTimeField(null=True)

    def decoded_headers(self):
        return json.loads(self.http_headers) if self.http_headers else {}

    def __unicode__(self):
        return u"<SourceScrapeFailure {0}>".format(self.source.url)

    def save(self, *args, **kwargs):
        super(SourceScrapeFailure, self).save(*args, **kwargs)
        self.source.last_failure = self
        self.source.save()

