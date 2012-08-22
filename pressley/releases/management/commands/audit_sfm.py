from __future__ import division
import sys
import random
import logging
from pprint import pprint
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from releases.models import Release
from superfastmatch.djangoclient import from_django_conf
from django.conf import settings


def random_sample(sample_size):
    release_count = Release.objects.count()

    if release_count == 0 or sample_size < 1:
        return []

    elif release_count <= sample_size:
        sample = list(Release.objects.all())

    elif release_count <= sample_size * 2:
        releases = list(Release.objects.all())
        sample = []
        while len(sample) < sample_size:
            r = random.randint(0, release_count - 1)
            if releases[r] is not None:
                sample.append(releases[r])
                releases[r] = None

    else:
        sampled_releases = set()
        sample = []
        while True:
            r = random.randint(0, release_count - 1)
            if r in sampled_releases:
                continue
            release = Release.objects.order_by('id')[r]
            if len(release.body.strip()) == 0:
                continue

            if r not in sampled_releases:
                sampled_releases.add(r)
                sample.append(release)
                if len(sample) == sample_size:
                    break

    return sample

class Command(BaseCommand):
    args = "sample_size"
    help = "Selects a random sample of press releases and compares the stored version with the superfastmatch server."
    option_list = BaseCommand.option_list + (
        make_option('--loglevel',
                    action='store',
                    choices=['debug', 'info', 'warning', 'error', 'critical'],
                    default='warning',
                    help='Logging level'),
    )

    def handle(self, sample_size, *args, **options):
        logging.basicConfig(level=getattr(logging, options['loglevel'].upper()))
        self.errors = set()

        try:
            sample_size = int(sample_size)
        except ValueError:
            raise CommandError("sample_size must be an integer.")

        self.sfm = from_django_conf()

        sample = random_sample(sample_size)
        for release in sample:
            self.check_release(release)

        
        log_fn = logging.error if len(self.errors) > 0 else logging.info
        log_fn(repr({
            'Sample size': len(sample),
            'Errors': len(self.errors),
            'Error rate': round(len(self.errors) / len(sample), 2)
        }))

    def check_release(self, release):
        doctype = release.source.doc_type or settings.DEFAULT_DOCTYPE

        try:
            doc = self.sfm.document(
                doctype=doctype,
                docid=release.id
            )
        except ValueError as e:
            raise CommandError("Unparseable response for document ({0},{1}): {2}".format(doctype, release.id, unicode(e)))

        if doc.get('success') != True:
            raise CommandError("Document ({0},{1}) is missing (should match release #{1})".format(doctype, release.id))

        def error(field):
            self.errors.add((release.id, doc['doctype'], doc['docid']))
            fmt = "{0} mismatch between release #{1} and doc ({2},{3})"
            raise CommandError(fmt.format(field, release.id,
                                          doc['doctype'], doc['docid']))

        if 'text' not in doc:
            raise CommandError("'text' not found in document ({0},{1})".format(release.source.doc_type or settings.DEFAULT_DOCTYPE,
                                                                               release.id))

        if release.body != doc['text']:
            error('text')

        if release.title != doc['title']:
            error('title')

        if release.source.organization != doc['source']:
            error('source')

