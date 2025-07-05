from django import forms
from .models import Agent

class CoordonneesGPSForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = ['latitude_centre', 'longitude_centre', 'rayon_metres', 'bureau']
        labels = {
            'latitude_centre': 'Latitude du centre du bureau',
            'longitude_centre': 'Longitude du centre du bureau',
            'rayon_metres': 'Rayon autorisé (mètres)',
            'bureau': 'Nom du bureau',
        }
