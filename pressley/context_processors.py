from django.conf import settings

def project_settings(request):
    ctx = {}
    ctx['deployment_name'] = getattr(settings, 'DEPLOYMENT_NAME', None)
    return ctx

