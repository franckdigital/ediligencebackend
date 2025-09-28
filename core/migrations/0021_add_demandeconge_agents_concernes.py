# Generated migration to add agents_concernes ManyToManyField to DemandeConge

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0020_rename_demandeconge_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='demandeconge',
            name='agents_concernes',
            field=models.ManyToManyField(blank=True, help_text='Agents de la même direction/service informés de ce congé', related_name='conges_concernes', to=settings.AUTH_USER_MODEL),
        ),
    ]
