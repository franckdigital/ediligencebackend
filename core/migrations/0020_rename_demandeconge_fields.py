# Generated migration to rename fields in DemandeConge model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_add_agents_concernes'),
    ]

    operations = [
        migrations.RenameField(
            model_name='demandeconge',
            old_name='created_at',
            new_name='date_creation',
        ),
        migrations.RenameField(
            model_name='demandeconge',
            old_name='updated_at',
            new_name='date_modification',
        ),
    ]
