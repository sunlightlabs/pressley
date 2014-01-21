from django import forms
from .models import Source

class SourceSearchForm(forms.Form):
    q = forms.CharField(max_length=255, required=False)

class SourceTestingForm(forms.Form):
    source_type = forms.IntegerField(required=True)
    url = forms.URLField(required=True)

