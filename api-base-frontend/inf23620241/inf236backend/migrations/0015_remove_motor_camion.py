# Generated by Django 4.2.11 on 2024-07-03 01:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inf236backend', '0014_camion_historialmotorcamion'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='motor',
            name='camion',
        ),
    ]
