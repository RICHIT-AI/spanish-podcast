# audio_processor/forms.py

from django import forms
from .models import PodcastGeneration

class CSVUploadForm(forms.ModelForm):
    class Meta:
        model = PodcastGeneration
        fields = ['csv_file']
        widgets = {
            'csv_file': forms.ClearableFileInput(attrs={'accept': '.csv'})
        }
