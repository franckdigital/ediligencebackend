from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0099_add_courrier_statut'),
    ]

    operations = [
        # Ajouter type_direction à Direction
        migrations.AddField(
            model_name='direction',
            name='type_direction',
            field=models.CharField(
                choices=[('cabinet', 'Cabinet'), ('direction_generale', 'Direction Générale'), ('direction', 'Direction')],
                default='direction',
                max_length=30,
                verbose_name='Type',
            ),
        ),
        # Modifier l'ordering de Direction
        migrations.AlterModelOptions(
            name='direction',
            options={'ordering': ['type_direction', 'nom'], 'verbose_name': 'Direction', 'verbose_name_plural': 'Directions'},
        ),
        # Supprimer la contrainte de limit_choices_to sur direction (pour la remplacer)
        migrations.AlterField(
            model_name='userprofile',
            name='direction',
            field=models.ForeignKey(
                blank=True, null=True,
                limit_choices_to={'type_direction': 'direction'},
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='profile_users',
                to='core.direction',
            ),
        ),
        # Ajouter cabinet FK
        migrations.AddField(
            model_name='userprofile',
            name='cabinet',
            field=models.ForeignKey(
                blank=True, null=True,
                limit_choices_to={'type_direction': 'cabinet'},
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='cabinet_users',
                to='core.direction',
            ),
        ),
        # Ajouter direction_generale FK
        migrations.AddField(
            model_name='userprofile',
            name='direction_generale',
            field=models.ForeignKey(
                blank=True, null=True,
                limit_choices_to={'type_direction': 'direction_generale'},
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='direction_generale_users',
                to='core.direction',
            ),
        ),
    ]
