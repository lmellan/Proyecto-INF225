# Generated by Django 4.2.11 on 2024-07-02 20:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inf236backend', '0012_remove_historialmotorcamion_camion_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mecanico',
            name='disponibilidad',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]