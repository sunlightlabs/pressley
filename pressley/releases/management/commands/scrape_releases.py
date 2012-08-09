from django.core.management.base import BaseCommand, CommandError
from releases.models import Release
from sources.models import Source
from readability.readability import Document
from lxml import etree, html
from dateutil.parser import parse
from datetime import datetime
from util import condense_whitespace
import requests
import superfastmatch
from settings import SUPERFASTMATCH



class Command(BaseCommand):
    args = '<none>'
    help = "Scrapes rss feeds in database for releases"
    
    def get_link_content(self, link):
        content = requests.get(link).content
        readable = Document(content)
        try:
            body = html.fromstring(readable.summary()).text_content()
        except:
            body = ''
        return condense_whitespace(body)


    def handle(self, *args, **kwargs):

        sfm = superfastmatch.Client(url=SUPERFASTMATCH['default'][0]['url'])
          
        sources = Source.objects.filter(source_type=2)

        for source in sources:
            #if source was scraped in the last 6 hours, don't hit it again
            if source.last_retrieved == None or (int(datetime.now().strftime("%s")) - int(source.last_retrieved.strftime("%s")) > 21600):
                print source.url
                feed = requests.get(source.url).content

                try:
                    feed_tree = etree.fromstring(feed)

                    for item in feed_tree.iter('item'):
                        source_name = source.organization
                        title = item.find('title').text 
                        try:
                            date = parse(item.find('pubDate').text)
                        except:
                            try:
                                date = parse(item.find('a10:updated').text)
                            except:
                                date = datetime.now()
                                
                        link = item.find('link').text
                        if link[-4:].lower() != ".pdf":
                            body = self.get_link_content(link)
                            release = Release.objects.get_or_create(url=link, title=title, date=date, body=body, source=source)[0]

                            #add to superfastmatch
                            response = None
                            try:
                                response = sfm.add(source.doc_type or SUPERFASTMATCH['default'][0]['doctype'], release.id, body, True, title=title, date=date, source=source.organization, put=False)
                                print response 
                                #update last retrieved for this source
                                source.last_retrieved = datetime.now()
                                source.save()
                            except superfastmatch.SuperFastMatchError as e:
                                if e.status == 200:
                                    print response 
                                    #update last retrieved for this source
                                    source.last_retrieved = datetime.now()
                                    source.save()
                                else:
                                    print "=================================================================="
                                    print "Problem parsing %s "  % source.url
                                    print e
                                    print "=================================================================="
                        else:
                            print "Could not store %s - item is a pdf" % link


                except Exception as e: 
                    print "=================================================================="
                    print "Problem parsing %s "  % source.url
                    print e
                    print "=================================================================="

            else:
                print "skipping %s because it was recently parsed (in the last 6 hours)" % source.url

