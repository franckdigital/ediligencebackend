import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Direction, Service, UserProfile

# Récupérer la Direction RH et un de ses services
direction_rh = Direction.objects.get(nom='Direction des Ressources Humaines')
service_recrutement = Service.objects.get(nom='Service Recrutement')

# Créer un utilisateur directeur
username = 'directeur_rh'
email = 'directeur.rh@example.com'

# Supprimer l'utilisateur s'il existe déjà
User.objects.filter(username=username).delete()

# Créer le nouvel utilisateur
user = User.objects.create_user(
    username=username,
    email=email,
    password='DirecteurRH2024!',
    first_name='Jean',
    last_name='Dupont'
)

# Créer le profil avec le rôle DIRECTEUR
profile = UserProfile.objects.create(
    user=user,
    role='DIRECTEUR',
    service=service_recrutement  # Le directeur est rattaché au service Recrutement
)

print(f"Utilisateur créé :")
print(f"- Nom d'utilisateur : {user.username}")
print(f"- Nom complet : {user.get_full_name()}")
print(f"- Email : {user.email}")
print(f"- Rôle : {profile.role}")
print(f"- Service : {profile.service}")
print(f"- Direction : {profile.service.direction}")
print("\nIdentifiants de connexion :")
print(f"- Nom d'utilisateur : {username}")
print(f"- Mot de passe : DirecteurRH2024!")
