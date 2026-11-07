import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0115_presence_depart_a_verifier_statut'),
    ]

    operations = [
        migrations.AlterField(
            model_name='geofencealert',
            name='bureau',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='geofence_alerts', to='core.bureau'),
        ),
    ]
