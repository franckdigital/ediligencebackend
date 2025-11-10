from django.contrib import admin
from .models import *

admin.site.register(UserProfile)

# --- MODULE AGENDA ---
admin.site.register(RendezVous)
admin.site.register(RendezVousDocument)
admin.site.register(Reunion)
admin.site.register(ReunionPresence)

# Register your models here.
