# Generated by Django 4.2.17 on 2025-06-04 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LieuEntreprise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(default='Siège', max_length=100)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('seuil_metres', models.FloatField(default=50)),
            ],
        ),
    ]
