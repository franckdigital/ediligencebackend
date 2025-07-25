# Generated by Django 4.2.23 on 2025-06-25 23:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_userprofile_matricule'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='agent',
            name='qr_code',
        ),
        migrations.RemoveField(
            model_name='presence',
            name='qr_code_data',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='qr_code',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='qr_secret',
        ),
        migrations.AddField(
            model_name='presence',
            name='empreinte_hash',
            field=models.TextField(blank=True, help_text="Hash de l'empreinte digitale scannée", null=True),
        ),
    ]
