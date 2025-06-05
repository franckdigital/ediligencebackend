from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_entreprise_lieuentreprise_entreprise_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='empreinte_hash',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
