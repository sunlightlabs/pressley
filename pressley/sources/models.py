from django.db import models

# Create your models here.

class Source(models.Model):

    SOURCE_TYPE_CHOICES = (
        (1, 'rss'),
        (2, 'rss-partial'),
        (3, 'html')
    )

    source_type = models.IntegerField(choices=SOURCE_TYPE_CHOICES)
    doc_type = models.IntegerField(null=True)
    organization = models.TextField(null=False)
    url = models.TextField(null=False)
    last_retrieved = models.DateTimeField(null=True)    



