from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile
import secrets
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Crée le profil UNIQUEMENT s'il n'existe pas déjà
    if created and not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=UserProfile)
def create_profile_fields(sender, instance, created, **kwargs):
    updated = False
    if created and not instance.matricule:
        instance.matricule = f"M{instance.id:05d}"
        updated = True
    if updated:
        instance.save()