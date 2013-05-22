from django.contrib import admin
from .models import Release

class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'title', 'url', 'created', 'updated')
    search_fields = ('title', 'date', 'url')
admin.site.register(Release, ReleaseAdmin)
