# Generated by Django 4.2.17 on 2025-06-06 15:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Courrier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=255, unique=True)),
                ('expediteur', models.CharField(max_length=255)),
                ('objet', models.TextField()),
                ('date_reception', models.DateField()),
                ('categorie', models.CharField(choices=[('Demande', 'Demande'), ('Invitation', 'Invitation'), ('Réclamation', 'Réclamation'), ('Autre', 'Autre')], default='Demande', max_length=64)),
                ('fichier_joint', models.FileField(blank=True, null=True, upload_to='courriers/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Diligence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference_courrier', models.CharField(max_length=255)),
                ('categorie', models.CharField(max_length=64)),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('en_cours', 'En cours de traitement'), ('en_correction', 'Demande de correction'), ('demande_validation', 'Demande de validation'), ('termine', 'Terminé'), ('archivee', 'Archivée')], default='en_attente', max_length=32)),
                ('fichier_joint', models.FileField(blank=True, max_length=500, null=True, upload_to='diligences/')),
                ('commentaires', models.TextField(blank=True, null=True)),
                ('commentaires_agents', models.TextField(blank=True, null=True)),
                ('instructions', models.TextField(blank=True, null=True)),
                ('nouvelle_instruction', models.TextField(blank=True, null=True)),
                ('date_limite', models.DateField(blank=True, null=True)),
                ('date_reception', models.DateField(blank=True, null=True)),
                ('expediteur', models.CharField(blank=True, max_length=255, null=True)),
                ('objet', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('archived_at', models.DateTimeField(blank=True, null=True)),
                ('validated_at', models.DateTimeField(blank=True, null=True)),
                ('agents', models.ManyToManyField(related_name='diligences', to=settings.AUTH_USER_MODEL)),
                ('archived_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diligences_archived', to=settings.AUTH_USER_MODEL)),
                ('courrier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diligences', to='core.courrier')),
            ],
        ),
        migrations.CreateModel(
            name='Direction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Direction',
                'verbose_name_plural': 'Directions',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='EtapeEvenement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_etape', models.CharField(max_length=255)),
                ('statut', models.CharField(max_length=64)),
                ('date_echeance', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Prestataire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('secteur_activite', models.CharField(max_length=255)),
                ('zone_geographique', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('telephone', models.CharField(max_length=32)),
                ('abonnement_actif', models.BooleanField(default=False)),
                ('profil_complet', models.TextField()),
                ('note_moyenne', models.FloatField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Projet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('dateDebut', models.DateField()),
                ('dateFinPrevue', models.DateField()),
                ('dateFinEffective', models.DateField(blank=True, null=True)),
                ('etat', models.CharField(choices=[('planifie', 'Planifié'), ('en_cours', 'En cours'), ('termine', 'Terminé'), ('suspendu', 'Suspendu')], default='planifie', max_length=20)),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('updatedAt', models.DateTimeField(auto_now=True)),
                ('agents', models.ManyToManyField(blank=True, limit_choices_to={'role': 'agent'}, related_name='agents', to=settings.AUTH_USER_MODEL)),
                ('directeurs', models.ManyToManyField(blank=True, limit_choices_to={'role': 'directeur'}, related_name='directeurs', to=settings.AUTH_USER_MODEL)),
                ('direction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.direction')),
                ('membres', models.ManyToManyField(blank=True, related_name='projets_membre', to=settings.AUTH_USER_MODEL)),
                ('responsable', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projets_responsable', to=settings.AUTH_USER_MODEL)),
                ('secretaires', models.ManyToManyField(blank=True, limit_choices_to={'role': 'secretaire'}, related_name='secretaires', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('direction', models.ForeignKey(blank=True, help_text='La direction à laquelle ce service appartient', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='services', to='core.direction')),
            ],
            options={
                'verbose_name': 'Service',
                'verbose_name_plural': 'Services',
                'ordering': ['direction__nom', 'nom'],
                'unique_together': {('nom', 'direction')},
            },
        ),
        migrations.CreateModel(
            name='Tache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('etat', models.CharField(choices=[('a_faire', 'À faire'), ('en_cours', 'En cours'), ('termine', 'Terminé'), ('bloque', 'Bloqué')], default='a_faire', max_length=20)),
                ('dateDebut', models.DateField(blank=True, null=True)),
                ('dateEcheance', models.DateField(blank=True, null=True)),
                ('priorite', models.CharField(choices=[('basse', 'Basse'), ('moyenne', 'Moyenne'), ('haute', 'Haute')], default='moyenne', max_length=10)),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('updatedAt', models.DateTimeField(auto_now=True)),
                ('agents', models.ManyToManyField(blank=True, limit_choices_to={'role': 'agent'}, related_name='agents_taches', to=settings.AUTH_USER_MODEL)),
                ('agentsAffectes', models.ManyToManyField(blank=True, related_name='taches_agent', to=settings.AUTH_USER_MODEL)),
                ('directeurs', models.ManyToManyField(blank=True, limit_choices_to={'role': 'directeur'}, related_name='directeurs_taches', to=settings.AUTH_USER_MODEL)),
                ('parentTache', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sous_taches', to='core.tache')),
                ('projet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='taches', to='core.projet')),
                ('responsable', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='taches_responsable', to=settings.AUTH_USER_MODEL)),
                ('secretaires', models.ManyToManyField(blank=True, limit_choices_to={'role': 'secretaire'}, related_name='secretaires_taches', to=settings.AUTH_USER_MODEL)),
                ('superieurs', models.ManyToManyField(blank=True, limit_choices_to={'role': 'superviseur'}, related_name='superieurs_taches', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('ADMIN', 'Admin'), ('DIRECTEUR', 'Directeur'), ('SUPERIEUR', 'Superieur'), ('AGENT', 'Agent'), ('SECRETAIRE', 'Secretaire'), ('PRESTATAIRE', 'Prestataire')], default='AGENT', max_length=20)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('qr_secret', models.CharField(editable=False, help_text='Clé secrète pour QR code signé', max_length=64, unique=True)),
                ('service', models.ForeignKey(blank=True, help_text="Le service auquel l'utilisateur est rattaché", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='core.service')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profil utilisateur',
                'verbose_name_plural': 'Profils utilisateurs',
            },
        ),
        migrations.CreateModel(
            name='TacheHistorique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=255)),
                ('details', models.TextField(blank=True, null=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('tache', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historiques', to='core.tache')),
                ('utilisateur', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('ADMIN', 'Admin'), ('DIRECTEUR', 'Directeur'), ('SUPERIEUR', 'Superieur'), ('AGENT', 'Agent'), ('SECRETAIRE', 'Secretaire'), ('PRESTATAIRE', 'Prestataire')], max_length=20)),
                ('permission', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'Role Permission',
                'verbose_name_plural': 'Role Permissions',
                'unique_together': {('role', 'permission')},
            },
        ),
        migrations.AddField(
            model_name='projet',
            name='service',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.service'),
        ),
        migrations.AddField(
            model_name='projet',
            name='superieurs',
            field=models.ManyToManyField(blank=True, limit_choices_to={'role': 'superviseur'}, related_name='superieurs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='PrestataireEtape',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('statut', models.CharField(max_length=64)),
                ('commission', models.DecimalField(decimal_places=2, max_digits=10)),
                ('etape', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.etapeevenement')),
                ('prestataire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.prestataire')),
            ],
        ),
        migrations.CreateModel(
            name='Observation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texte', models.TextField()),
                ('date_observation', models.DateTimeField(auto_now_add=True)),
                ('auteur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('diligence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.diligence')),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ImputationFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(blank=True, null=True, upload_to='imputation_files/')),
                ('sfdt_content', models.TextField(blank=True, help_text='Contenu du document Word au format Syncfusion SFDT', null=True)),
                ('mode', models.CharField(choices=[('lecture_seule', 'Lecture seule'), ('intervenant', 'Intervenant')], default='lecture_seule', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imputation_files', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='imputation_files_created', to=settings.AUTH_USER_MODEL)),
                ('diligence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imputation_files', to='core.diligence')),
            ],
        ),
        migrations.CreateModel(
            name='Fichier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('url', models.URLField()),
                ('type', models.CharField(max_length=100)),
                ('taille', models.IntegerField()),
                ('projet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fichiers', to='core.projet')),
                ('tache', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fichiers', to='core.tache')),
            ],
        ),
        migrations.CreateModel(
            name='Evenement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255)),
                ('lieu', models.CharField(max_length=255)),
                ('date_debut', models.DateField()),
                ('date_fin', models.DateField()),
                ('statut', models.CharField(max_length=64)),
                ('organisateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Evaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.IntegerField()),
                ('commentaire', models.TextField()),
                ('date_evaluation', models.DateTimeField(auto_now_add=True)),
                ('prestataire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.prestataire')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='etapeevenement',
            name='evenement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.evenement'),
        ),
        migrations.AddField(
            model_name='etapeevenement',
            name='responsable',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='diligence',
            name='direction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diligences', to='core.direction'),
        ),
        migrations.AddField(
            model_name='diligence',
            name='services_concernes',
            field=models.ManyToManyField(related_name='diligences_concernes', to='core.service'),
        ),
        migrations.AddField(
            model_name='courrier',
            name='service',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courriers', to='core.service'),
        ),
        migrations.CreateModel(
            name='Commentaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenu', models.TextField()),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('auteur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commentaires', to=settings.AUTH_USER_MODEL)),
                ('tache', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commentaires', to='core.tache')),
            ],
        ),
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('prenom', models.CharField(blank=True, max_length=255, null=True)),
                ('telephone', models.CharField(blank=True, max_length=30, null=True)),
                ('matricule', models.CharField(max_length=100, unique=True)),
                ('qr_code', models.TextField(blank=True, null=True)),
                ('poste', models.CharField(max_length=100)),
                ('bureau', models.CharField(blank=True, max_length=100, null=True)),
                ('latitude_centre', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude_centre', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('rayon_metres', models.IntegerField(blank=True, help_text='Rayon de la zone autorisée en mètres', null=True)),
                ('role', models.CharField(choices=[('ADMIN', 'Admin'), ('DIRECTEUR', 'Directeur'), ('SUPERIEUR', 'Superieur'), ('AGENT', 'Agent'), ('SECRETAIRE', 'Secretaire'), ('PRESTATAIRE', 'Prestataire')], default='AGENT', max_length=20)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.service')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='agent_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Presence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_presence', models.DateField()),
                ('heure_arrivee', models.TimeField(blank=True, null=True)),
                ('heure_depart', models.TimeField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('présent', 'Présent'), ('absent', 'Absent'), ('en mission', 'En mission'), ('permission accordée', 'Permission accordée')], max_length=32)),
                ('qr_code_data', models.TextField(blank=True, help_text='Donnée brute du QR code scannée', null=True)),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=10)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=10)),
                ('localisation_valide', models.BooleanField(default=False)),
                ('commentaire', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='presences', to='core.agent')),
            ],
            options={
                'verbose_name': 'Présence',
                'verbose_name_plural': 'Présences',
                'ordering': ['-date_presence', '-heure_arrivee'],
                'unique_together': {('agent', 'date_presence')},
            },
        ),
        migrations.CreateModel(
            name='ImputationAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_type', models.CharField(choices=[('view', 'Lecture'), ('edit', 'Édition')], default='view', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('validated_at', models.DateTimeField(blank=True, null=True)),
                ('archived_at', models.DateTimeField(blank=True, null=True)),
                ('archived_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diligences_archivees', to=settings.AUTH_USER_MODEL)),
                ('diligence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imputation_access', to='core.diligence')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imputation_access', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('diligence', 'user', 'access_type')},
            },
        ),
    ]
