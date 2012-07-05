from django.core.management.base import BaseCommand, CommandError
from sources.models import Source
import csv

class Command(BaseCommand):
    args = '<file_name>'
    help = "Loads sources from a csv. Specify the file location at runtime"
    
    def handle(self, *args, **kwargs):
        try:
            reader = csv.reader(open(args[0]))
            logger = csv.writer(open('source_errors.log', 'a'))
            
            if len(args) > 1:
                doc_type = args[1]
            else:
                doc_type = None

            for line in reader:
                try:
                    organization = line[1]
                    rss_ = line[2]
    
                    if organization:
                        if rss_.strip() == 'Y':
                            source_type = 2 
                            url = line[4]
                            obj, created = Source.objects.get_or_create(organization=organization.strip(), url=url, source_type=source_type, doc_type=doc_type)

                        elif rss_.strip() == 'N':
                            source_type = 3
                            url = line[4]
                            obj, created = Source.objects.get_or_create(organization=organization.strip(), url=url, source_type=source_type, doc_type=doc_type) 

                        elif rss_.strip() == 'M':

                            for u in line[4:]:
                                url = u
                                source_type = 2
                                obj, created = Source.objects.get_or_create(organization=organization.strip(), url=url, source_type=source_type, doc_type=doc_type) 

                        else:
                            logger.writerow(line)

                except Exception as e:
                    print "row error - %s" % e
                    #row error
        except:
            print "There is no such file %s" % args[0]

