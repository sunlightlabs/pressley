from __future__ import division
from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Source
from .forms import SourceTestingForm, SourceSearchForm



def status_list(request):
    failed_sources = Source.objects.filter(last_failure__isnull=False, last_failure__resolved__isnull=True)
    exports = {
        'failed_rows': failed_sources,
        'failed_row_count': len(failed_sources)
    }
    return render(request, 'sources/statuses.html', exports)


def source_history(request, source_id):
    source = get_object_or_404(Source, pk=source_id)
    exports = {
        'source': source,
        'failures': source.scrape_failures.all()
    }
    return render(request, 'sources/source_history.html', exports)

def index(request):
    search_form = SourceSearchForm(request.GET)
    if search_form.is_valid() and search_form.cleaned_data['q']:
        sources = Source.objects.filter(organization__icontains=search_form.cleaned_data['q'])
    else:
        sources = Source.objects.all()

    sources_found = list(sources.order_by('organization'))
    source_count = sources.count()
    org_count = sources.values('organization').distinct().count()

    ctx = {
        'search_form': search_form,
        'sources_found': sources_found,
        'source_count': source_count,
        'org_count': org_count
    }
    return render(request, 'sources/index.html', ctx)

@login_required
def test_source(request):
    ctx = {}

    if request.method == 'POST':
        form = SourceTestingForm(request.POST)
        if form.is_valid():
            pass
    else:
        form = SourceTestingForm()

    ctx['form'] = form
    return render(request, 'sources/test.html', ctx)
