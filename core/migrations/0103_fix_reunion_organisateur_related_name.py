from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0102_tache_agenda_links'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='reunion',
            name='organisateur',
            field=models.ForeignKey(
                help_text='Directeur ou sous-directeur',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='agenda_reunions_organisees',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
