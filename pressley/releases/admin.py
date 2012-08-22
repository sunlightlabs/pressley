from django.contrib import admin
from .models import Release

class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'url')
admin.site.register(Release, ReleaseAdmin)
