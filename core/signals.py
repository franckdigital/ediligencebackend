from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User  # adapte si ton modèle s'appelle différemment

@receiver(post_save, sender=User)
def create_matricule_qrcode(sender, instance, created, **kwargs):
    updated = False
    if created and not instance.matricule:
        instance.matricule = f"M{instance.id:05d}"
        updated = True
    if created and not instance.qr_code:
        instance.qr_code = f"QR{instance.id:05d}"
        updated = True
    if updated:
        instance.save()