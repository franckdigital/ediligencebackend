"""
Seed de données de l'application eDiligence — TOUT SAUF le pointage.

Crée : structure organisationnelle, utilisateurs/profils, sites et paliers,
courriers, diligences, congés/absences, réunions/rendez-vous, projets/tâches,
GED, fiches personnel RH.

N'écrit JAMAIS dans les tables de pointage : Presence, Agent, Bureau,
AgentLocation, GeofenceAlert, GeofenceSettings, OccurrenceSpeciale, DeviceLock.

Idempotent (get_or_create) : peut être relancé sans doublons.

Usage :
    python manage.py seed_data
    python manage.py seed_data --password "MotDePasse"   (défaut : Lanema2024!)
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.management.commands.seed_medi import Command as MediSeed


class Command(BaseCommand):
    help = "Alimente la base avec les données de l'application (hors pointage)"

    def add_arguments(self, parser):
        parser.add_argument("--password", default=None,
                            help="Mot de passe à appliquer aux comptes créés par le seed")

    def handle(self, *args, **options):
        from core.models import (Presence, Agent, Bureau, AgentLocation,
                                 GeofenceAlert, OccurrenceSpeciale, DeviceLock)

        pointage_models = (Presence, Agent, Bureau, AgentLocation,
                           GeofenceAlert, OccurrenceSpeciale, DeviceLock)
        avant = {m.__name__: m.objects.count() for m in pointage_models}

        self.stdout.write(self.style.MIGRATE_HEADING("=== SEED DONNÉES eDILIGENCE (hors pointage) ==="))

        seed = MediSeed(stdout=self.stdout._out, stderr=self.stderr._out)
        seed.stdout = self.stdout
        seed.style = self.style
        seed._structure()
        seed._users()
        self._sites()
        seed._courriers()
        seed._diligences()
        seed._conges_absences()
        seed._reunions_rdv()
        seed._projets_taches()
        seed._ged()
        seed._personnel()
        self._comptes(options.get("password"))

        apres = {m.__name__: m.objects.count() for m in pointage_models}
        if apres != avant:
            self.stderr.write(self.style.ERROR(f"ATTENTION : tables de pointage modifiées {avant} -> {apres}"))
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ Aucune donnée de pointage créée"))

        self.stdout.write(self.style.SUCCESS("\n=== SEED TERMINÉ ==="))
        self.stdout.write("  Comptes : dr.medi, dg.lanema, sec.lanema, aya.kone, jean.brou, fatou.diallo, admin.lanema")

    def _sites(self):
        from core.models import Site, SitePalier
        self.stdout.write("  → Sites et paliers…")
        siege, _ = Site.objects.get_or_create(
            code="LANEMA-SIEGE",
            defaults={"nom": "LANEMA — Siège Abidjan", "type_site": "siege", "ville": "Abidjan",
                      "commune": "Plateau", "adresse": "Rue du Commerce, Plateau, Abidjan"})
        Site.objects.get_or_create(
            code="LANEMA-BOUAKE",
            defaults={"nom": "LANEMA — Antenne Bouaké", "type_site": "antenne", "ville": "Bouaké"})
        for ordre, nom in enumerate(["Rez-de-chaussée", "1er étage", "2ème étage"]):
            SitePalier.objects.get_or_create(site=siege, nom=nom, defaults={"ordre": ordre})
        self.stdout.write(self.style.SUCCESS("    ✓ 2 sites + 3 paliers"))

    def _comptes(self, password):
        admin = User.objects.filter(username="admin.lanema").first()
        if admin and not admin.is_superuser:
            admin.is_superuser = True
            admin.is_staff = True
            admin.save()
        if password:
            for u in User.objects.filter(username__in=[
                    "dr.medi", "dg.lanema", "sec.lanema", "aya.kone", "jean.brou",
                    "fatou.diallo", "admin.lanema"]):
                u.set_password(password)
                u.save()
            self.stdout.write(self.style.SUCCESS("    ✓ Mot de passe personnalisé appliqué"))
