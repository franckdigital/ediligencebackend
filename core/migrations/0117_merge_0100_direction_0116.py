from django.db import migrations


class Migration(migrations.Migration):
    """Fusionne les deux branches issues de 0099 (deux migrations 0100)."""

    dependencies = [
        ('core', '0100_direction_type_userprofile_cabinet_dg'),
        ('core', '0116_geofencealert_bureau_nullable'),
    ]

    operations = []
