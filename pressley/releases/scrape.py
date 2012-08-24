# -*- coding: utf-8 -*-

import requests
import dateutil.parser
from util import kill_control_characters, readability_extract
from now import now
from releases.models import Release

def get_link_content(link):
    response = requests.get(link)
    if response.status_code != 200:
        raise Exception("Unable to fetch release content: {0}".format(link))

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

