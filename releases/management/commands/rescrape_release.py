# -*- coding: utf-8 -*-

import logging
from django.core.management.base import BaseCommand, CommandError
from releases.models import Release
from pressley.now import now
from pressley.util import kill_control_characters
from releases.scrape import get_link_content
from superfastmatch.djangoclient import from_django_conf
from django.conf import settings


class Command(BaseCommand):
    args = "<release URLs>"
    help = "Re-scrape the body of a given press release."

    def handle(self, *args, **options):
        if not hasattr(settings, 'SUPERFASTMATCH'):
            raise CommandError('You must configure SUPERFASTMATCH in your project settings.')

        self.sfm = from_django_conf()

        for url in args:
            try:
                if url.startswith('http://') or url.startswith('https://'):
                    release = Release.objects.get(url=url)
                    body = get_link_content(release.url)
                    release.title = kill_control_characters(release.title)
                    release.body = body
                    release.updated = now()
                    release.save()
                    logging.info("Updated release {0}: {1}".format(release.id, release.url))
                else:
                    logging.warning("Skipping non-HTTP link {0}".format(release.url))
            except Exception as e:
                logging.error("Failed to rescrape {0}: {1}".format(url, str(e)))



