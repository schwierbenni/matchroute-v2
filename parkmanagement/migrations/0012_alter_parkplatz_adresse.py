# Generated by Django 5.1.7 on 2025-07-21 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkmanagement', '0011_alter_parkplatz_options_parkplatz_external_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parkplatz',
            name='adresse',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
