from django.contrib import admin
from .models import Release

class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'title', 'url', 'created', 'updated')
admin.site.register(Release, ReleaseAdmin)
