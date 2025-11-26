# Generated migration for adding statut field to Courrier model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0043_courrierrappel_courrierstatut_courriernotification'),  # Ajustez selon votre dernière migration
    ]

    operations = [
        migrations.AddField(
            model_name='courrier',
            name='statut',
            field=models.CharField(
                choices=[
                    ('nouveau', 'Nouveau'),
                    ('en_attente', 'En Attente'),
                    ('en_cours', 'En Cours'),
                    ('traite', 'Traité'),
                    ('termine', 'Terminé'),
                    ('archive', 'Archivé')
                ],
                default='nouveau',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='courrier',
            name='date_traitement',
            field=models.DateField(blank=True, null=True),
        ),
    ]
