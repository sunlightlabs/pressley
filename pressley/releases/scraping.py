import requests

from lxml import html
from readability.readability import Document

from util import condense_whitespace

def get_link_content(link):
    content = requests.get(link).content
    readable = Document(content)
    body = html.fromstring(readable.summary()).text_content()
    title = readable.title()
    return (title, condense_whitespace(body))

