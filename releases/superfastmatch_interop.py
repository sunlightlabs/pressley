import logging
from superfastmatch import SuperFastMatchError

def post_release_to_superfastmatch(release, sfm, doctype):
    """
    Posts the given press release to the superfastmatch server.
    Returns True if it was posted, None otherwise.
    """

    if release.body is None or len(release.body.strip()) == 0:
        logging.info("Skipping release #{0} because it has an empty body.".format(release.id))
        return

    try:
        result = sfm.add(doctype=doctype,
                         docid=release.id,
                         url=release.url,
                         text=release.body,
                         title=release.title,
                         date=release.date,
                         source=release.source.organization,
                         defer=True)
        if result.get('success') == True:
            logging.info(u"Posted release {0} to superfastmatch doctype {1}".format(release.id, doctype))
            return True

        else:
            logging.error(u"Failed to add release #{0} to superfastmatch doctype {1}: {2}".format(release.id, doctype, result.get('error')))

    except SuperFastMatchError as e:
        logging.error(u"Failed to add release #{0} to superfastmatch doctype {1}: {2}".format(release.id, doctype, unicode(e)))

