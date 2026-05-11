from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0109_add_site_palier'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='org_unit_key',
            field=models.CharField(
                blank=True, null=True, max_length=255,
                help_text="Clé de l'unité organisationnelle liée (organigramme)"
            ),
        ),
        migrations.AddField(
            model_name='site',
            name='org_unit_label',
            field=models.CharField(
                blank=True, null=True, max_length=255,
                help_text="Libellé de l'unité organisationnelle liée"
            ),
        ),
    ]
