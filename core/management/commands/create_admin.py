from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile

class Command(BaseCommand):
    help = 'Crée un super utilisateur avec le rôle ADMIN'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('--first_name', type=str, default='')
        parser.add_argument('--last_name', type=str, default='')

    def handle(self, *args, **options):
        try:
            # Vérifier si l'utilisateur existe déjà
            if User.objects.filter(username=options['username']).exists():
                self.stdout.write(self.style.ERROR(f"Un utilisateur avec le nom {options['username']} existe déjà"))
                return

            # Créer l'utilisateur
            user = User.objects.create_user(
                username=options['username'],
                email=options['email'],
                password=options['password'],
                first_name=options['first_name'],
                last_name=options['last_name'],
                is_staff=True,
                is_superuser=True,
                is_active=True
            )

            # Créer le profil avec le rôle ADMIN
            UserProfile.objects.create(user=user, role='ADMIN')

            self.stdout.write(self.style.SUCCESS(f"Super utilisateur {options['username']} créé avec succès"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de la création de l'utilisateur : {str(e)}"))
