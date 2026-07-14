# Generated for absence prolongée (>1h) detection, tracing and last known position

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0112_add_courrier_ia_ocr_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='geofencealert',
            name='duree_hors_zone_minutes',
            field=models.IntegerField(blank=True, help_text="Durée continue (en minutes) pendant laquelle l'agent est resté hors de la zone autorisée", null=True),
        ),
        migrations.AddField(
            model_name='geofencealert',
            name='trace_positions',
            field=models.JSONField(blank=True, help_text="Historique des positions GPS ([{latitude, longitude, timestamp, distance_metres}, ...]) relevées pendant l'absence", null=True),
        ),
        migrations.AlterField(
            model_name='geofencealert',
            name='type_alerte',
            field=models.CharField(choices=[('sortie_zone', 'Sortie de zone'), ('entree_zone', 'Entrée en zone'), ('hors_horaires', 'Hors horaires de travail'), ('absence_prolongee', 'Absence prolongée (>1h)')], default='sortie_zone', max_length=20),
        ),
        migrations.AddField(
            model_name='geofencesettings',
            name='seuil_absence_prolongee_minutes',
            field=models.IntegerField(default=60, help_text="Durée continue (en minutes) hors de la zone du site au-delà de laquelle une absence prolongée est détectée, tracée et notifiée (défaut : 60 min = 1h)"),
        ),
        migrations.AddField(
            model_name='presence',
            name='derniere_latitude_connue',
            field=models.DecimalField(blank=True, decimal_places=6, help_text="Latitude de la dernière position connue de l'agent pendant son absence", max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='presence',
            name='derniere_longitude_connue',
            field=models.DecimalField(blank=True, decimal_places=6, help_text="Longitude de la dernière position connue de l'agent pendant son absence", max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='presence',
            name='trace_absence',
            field=models.JSONField(blank=True, help_text="Historique des positions GPS ([{latitude, longitude, timestamp, distance_metres}, ...]) relevées depuis le début de l'absence", null=True),
        ),
    ]
