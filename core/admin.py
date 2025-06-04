from django.contrib import admin
from .models import *

@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ('nom',)

@admin.register(LieuEntreprise)
class LieuEntrepriseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'entreprise', 'latitude', 'longitude', 'seuil_metres')

admin.site.register(UserProfile)

# Register your models here.
