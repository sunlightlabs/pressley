# -*- coding: utf-8 -*-

import requests
import logging
import dateutil.parser
from mimeparse import parse_mime_type
from pressley.util import kill_control_characters, readability_extract
from pressley.now import now
from releases.models import Release

def get_link_content(link):
    try:
        response = requests.get(link)
        if response.status_code == 400:
            logging.warn(u"404 {}".format(link))
            return None
        if response.status_code != 200:
            raise Exception(u"Unable to fetch release content: {0}".format(link))
    except requests.exceptions.InvalidURL as e:
        logging.warn(u"Invalid link {0}: {1}".format(link, unicode(e)))
        return None

    content_type = response.headers.get('content-type')
    if not content_type:
        logging.warn(u"Response did not contain a Content-Type header: {0}".format(link))
        return None

    (mime_type, mime_subtype, mt_params) = parse_mime_type(content_type)
    if mime_type != 'text' or mime_subtype not in ('html', 'xhtml'):
        logging.warn(u"Skipping non-HTML link: {0}".format(link))
        return None

    if len(response.content) == 0:
        logging.warn(u"Server returned an empty body: {0}".format(link))
        return None

    (title, body) = readability_extract(response.content)
    return kill_control_characters(body)

def scrape_release(source, feed, entry, link):
    title_text = entry.get('title')
    if not isinstance(title_text, unicode):
        title_text = title_text.encode('utf-8', 'ignore')
    title = kill_control_characters(title_text)
    date_text = (entry.get('published') or
                 entry.get('updated') or
                 entry.get('a10:updated'))
    date = dateutil.parser.parse(date_text) if date_text else now()
    body = get_link_content(link)
    if body is None:
        return

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

