from urlparse import urlparse

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def url_abbrev(urlstr, limit=38):
    parsed = urlparse(urlstr)
    host = parsed.netloc
    if host.startswith("www."):
        host = host[4:]
    abbr = u"{h}{p}".format(h=host,
                            p=parsed.path)
    if len(abbr) > limit:
        abbr = abbr[0:max(5, limit-3)] + "..."
    return abbr

