from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0113_absence_prolongee_tracking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='geofencealert',
            name='type_alerte',
            field=models.CharField(choices=[('sortie_zone', 'Sortie de zone'), ('entree_zone', 'Entrée en zone'), ('hors_horaires', 'Hors horaires de travail'), ('absence_prolongee', 'Absence prolongée (>1h)'), ('gps_inactif', 'GPS inactif / désactivé')], default='sortie_zone', max_length=20),
        ),
        migrations.AlterField(
            model_name='geofencealert',
            name='latitude_agent',
            field=models.DecimalField(blank=True, decimal_places=17, max_digits=22, null=True),
        ),
        migrations.AlterField(
            model_name='geofencealert',
            name='longitude_agent',
            field=models.DecimalField(blank=True, decimal_places=17, max_digits=22, null=True),
        ),
        migrations.AlterField(
            model_name='geofencealert',
            name='distance_metres',
            field=models.IntegerField(blank=True, help_text='Distance en mètres par rapport au centre du bureau (inconnue si GPS inactif)', null=True),
        ),
        migrations.AddField(
            model_name='geofencesettings',
            name='seuil_gps_inactif_minutes',
            field=models.IntegerField(default=30, help_text="Durée (en minutes) sans aucune position GPS reçue d'un agent présent au-delà de laquelle une alerte 'GPS inactif' est levée — évite qu'un agent désactivant sa localisation devienne invisible à la détection de sortie (défaut : 30 min)"),
        ),
    ]
