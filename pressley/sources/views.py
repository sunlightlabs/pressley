from __future__ import division
from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from .models import Source



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
