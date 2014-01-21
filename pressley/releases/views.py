from __future__ import division

import re

from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .scraping import get_link_content
from .forms import ReleaseTestingForm


@login_required
def test_release(request):
    ctx = {
        'form': None,
        'paragraphs': None,
        'title': None
    }

    if request.method == 'POST':
        form = ReleaseTestingForm(request.POST)
        if form.is_valid():
            (title, text) = get_link_content(form.cleaned_data['url'])
            ctx['title'] = title
            ctx['paragraphs'] = re.split(ur'[\r\n]+', text, re.S)

    else:
        form = ReleaseTestingForm()

    ctx['form'] = form
    return render(request, 'releases/test.html', ctx)
