from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0114_gps_inactif_alert'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presence',
            name='statut',
            field=models.CharField(choices=[('présent', 'Présent'), ('absent', 'Absent'), ('en mission', 'En mission'), ('permission accordée', 'Permission accordée'), ('depart_a_verifier', 'Départ à vérifier')], max_length=32),
        ),
    ]
