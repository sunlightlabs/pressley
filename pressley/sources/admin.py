from django.contrib import admin
from .models import Source, SourceScrapeFailure

class SourceScrapeFailureAdmin(admin.ModelAdmin):
    list_display = ['id', 'timestamp', 'resolved', 'source', 'description', 'http_status']
    ordering = ['-timestamp', 'source']
    readonly_fields = ['source', 'description', 'http_status', 'http_body', 'http_headers', 'timestamp', 'resolved']

    fieldsets = (
        ('Basics', {
            'fields': ('source', 'description')
        }),
        ('Status', {
            'fields': ('timestamp', 'resolved')
        }),
        ('Details', {
            'fields': ('http_status', 'http_body', 'http_headers')
        })
    )

admin.site.register(SourceScrapeFailure, SourceScrapeFailureAdmin)

class SourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'source_type', 'doc_type', 'organization', 'last_retrieved', 'url']
    ordering = ['organization']
    readonly_fields = ['last_retrieved', 'last_failure']

admin.site.register(Source, SourceAdmin)

