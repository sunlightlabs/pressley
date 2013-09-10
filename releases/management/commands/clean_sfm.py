from __future__ import division
import logging
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from releases.models import Release
from superfastmatch.djangoclient import from_django_conf
from superfastmatch.iterators import DocumentIterator
from django.conf import settings

class Command(BaseCommand):
    args = ''
    help = "Iterates over documents on a superfastmatch server and deletes those that do not have a corresponding press release."
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    action='store_true',
                    dest='dry_run',
                    default=False,
                    help='Don\'t actually delete anything.'),
        make_option('--doctype',
                    action='store',
                    dest='doctype',
                    default=None,
                    help='Doctype(s) to limit the examination to (e.g. 1:3-5:9)'),
    )

    def handle(self, *args, **options):
        self.errors = set()

        sfm = from_django_conf()

        docs = DocumentIterator(sfm, order_by='docid',
                                doctype=options['doctype'],
                                chunksize=1000,
                                fetch_text=False)

        try:
            for doc in docs:
                try:
                    release = Release.objects.get(id=doc['docid'])
                    doctype = release.source.doc_type or settings.DEFAULT_DOCTYPE
                    if doctype != doc['doctype']:
                        logging.warning("Doctype mismatch for document ({0[doctype]},{0[docid]}) and release #{1.id} (source: {1.source}, doctype: {2}).".format(doc, release, doctype))

                except Release.DoesNotExist:
                    if options['dry_run'] == False:
                        sfm.delete(doc['doctype'], doc['docid'])
                        logging.warning("Deleting document ({0[doctype]},{0[docid]}) because there is no corresponding press release.".format(doc))
                    else:
                        logging.warning("Document ({0[doctype]},{0[docid]}) does not have a corresponding press release.".format(doc)) 

        except ValueError:
            logging.error("Failed on document {0},{1}".format(doc['doctype'], doc['docid']))

