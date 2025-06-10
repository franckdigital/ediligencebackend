from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile
import secrets
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

# 1. Création automatique du profil à la création d'un User
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# 2. Génération automatique du matricule, qr_secret et QR code image
@receiver(post_save, sender=UserProfile)
def create_profile_fields(sender, instance, created, **kwargs):
    updated = False

    if created and not instance.matricule:
        instance.matricule = f"M{instance.id:05d}"
        updated = True
    if created and not instance.qr_secret:
        instance.qr_secret = secrets.token_hex(32)
        updated = True

    # Génération du QR code image à partir du matricule ou du qr_secret
    if (created or not instance.qr_code) and instance.qr_secret:
        qr_data = f"{instance.matricule}|{instance.qr_secret}"
        qr_img = qrcode.make(qr_data)
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        file_name = f"qrcode_{instance.user.username}.png"
        instance.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)
        updated = True

    if updated:
        instance.save()