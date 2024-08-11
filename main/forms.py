from django import forms
from django.forms import ModelForm
from main.models import Team,Iframe


class TeamForm(ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'password', 'type', 'email']


class DocumentForm(forms.Form):
    file = forms.FileField(
            label='Select a file',
            help_text='max. 200 megabytes'
    )

class IframeForm(ModelForm):
    class Meta:
        model = Iframe
        fields = ['name', 'url', 'icon']
