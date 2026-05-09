from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile


class Command(BaseCommand):
    help = 'Assure que tous les superusers ont le rôle ADMIN dans leur profil'

    def handle(self, *args, **options):
        superusers = User.objects.filter(is_superuser=True)
        fixed = 0
        for user in superusers:
            profile, created = UserProfile.objects.get_or_create(
                user=user, defaults={'role': 'ADMIN'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"Profil créé avec ADMIN pour {user.username}"
                ))
                fixed += 1
            elif profile.role != 'ADMIN':
                profile.role = 'ADMIN'
                profile.save(update_fields=['role'])
                self.stdout.write(self.style.SUCCESS(
                    f"Role mis a jour -> ADMIN pour {user.username}"
                ))
                fixed += 1
            else:
                self.stdout.write(f"{user.username} : déjà ADMIN")
        self.stdout.write(self.style.SUCCESS(
            f"\n{fixed} profil(s) mis à jour sur {superusers.count()} superuser(s)."
        ))
