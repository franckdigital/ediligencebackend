from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0101_alter_bureau_latitude_centre_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tache',
            name='reunions',
            field=models.ManyToManyField(
                blank=True,
                related_name='taches',
                to='core.reunion',
                verbose_name='Réunions liées',
            ),
        ),
        migrations.AddField(
            model_name='tache',
            name='rendezvous_lies',
            field=models.ManyToManyField(
                blank=True,
                related_name='taches',
                to='core.rendezvous',
                verbose_name='Rendez-vous liés',
            ),
        ),
    ]
