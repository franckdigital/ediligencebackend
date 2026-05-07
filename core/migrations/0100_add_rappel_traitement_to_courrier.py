# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0099_add_courrier_statut'),
    ]

    operations = [
        migrations.AddField(
            model_name='courrier',
            name='rappel_traitement',
            field=models.BooleanField(default=False, help_text='Activer les rappels automatiques de traitement'),
        ),
    ]
