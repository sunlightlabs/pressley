from django.db import models

class Release(models.Model):

    source = models.ForeignKey('sources.Source')
    date = models.DateField(auto_now=False, null=False)
    url = models.TextField(null=False, unique=True)
    title = models.TextField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True, null=True)

    class Meta:
        ordering = ['-date', 'source']

    def __unicode__(self):
        return u"{0.url} from {0.source}".format(self)
