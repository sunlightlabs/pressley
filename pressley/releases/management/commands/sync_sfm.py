import os
import json
import logging
import dateutil.parser
from django.core.management.base import BaseCommand, CommandError
from releases.models import Release
from django.conf import settings
from optparse import make_option
from now import now
from releases.superfastmatch_interop import post_release_to_superfastmatch
from superfastmatch.djangoclient import from_django_conf

CheckpointPath = os.path.join(settings.PROJECT_ROOT,
                              'sync_sfm_checkpoint.json')

class Command(BaseCommand):
    args = '[release id [release id [release id...]]]'
    help = "Posts press releases in pressley to sfm"
    option_list = BaseCommand.option_list + (
        make_option('--all',
                    action='store_true',
                    dest='all',
                    default=False,
                    help='Sync all releases, not just those since the last run.'),
        make_option('--loglevel',
                    action='store',
                    choices=['debug', 'info', 'warning', 'error', 'critical'],
                    default='warning',
                    help='Logging level'),
    )

    def read_checkpoint(self):
        """
        Reads in the timestamp of the last run.
        """
        self.starttime = now()
        if not os.path.exists(CheckpointPath):
            self.checkpoint = {
                'timestamp': now()
            }
        else:
            with file(CheckpointPath, 'r') as checkpoint_file:
                self.checkpoint = json.load(checkpoint_file)
                self.checkpoint['timestamp'] = dateutil.parser.parse(self.checkpoint['timestamp'])
        logging.info("Last run: {0}".format(self.checkpoint['timestamp']))

    def write_checkpoint(self):
        """
        Writes the current time to the checkpoint file for reference
        by future invocations.
        """
        with file(CheckpointPath, 'w') as checkpoint_file:
            self.checkpoint['timestamp'] = self.starttime.isoformat()
            json.dump(self.checkpoint, checkpoint_file)

    def handle(self, *args, **options):
        logging.basicConfig(level=getattr(logging, options['loglevel'].upper()))

        if not hasattr(settings, 'SUPERFASTMATCH'):
            raise CommandError('You must configure SUPERFASTMATCH in your project settings.')

        if not hasattr(settings, 'DEFAULT_DOCTYPE'):
            raise CommandError('You must specify a DEFAULT_DOCTYPE in your project settings.')

        self.sfm = from_django_conf()

        self.read_checkpoint()

        if len(args) == 0:
            releases = Release.objects.order_by('-created', 'id')
            if options['all'] == False:
                releases = Release.objects.filter(updated__gte=self.checkpoint['timestamp'])
        else:
            try:
                release_ids = [int(rid) for rid in args]
                releases = Release.objects.filter(id__in=release_ids)
            except ValueError:
                raise CommandError("All release ids must be integers.")

        logging.info("Synchronizing {0} releases".format(len(releases)))
        if Release.objects.count() > 0:
            logging.info("Most recent press release: {0}".format(Release.objects.order_by('-updated')[0].updated))
        for r in releases:
            doctype = r.source.doc_type or settings.DEFAULT_DOCTYPE
            post_release_to_superfastmatch(r, self.sfm, doctype)

        self.write_checkpoint()


    
