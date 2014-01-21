from django import forms

class ReleaseTestingForm(forms.Form):
    url = forms.URLField(required=True)

