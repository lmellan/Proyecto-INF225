# Generated by Django 4.2.11 on 2024-06-06 02:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inf236backend', '0003_camion_sistema_historialmotorcamion'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mecanico',
            name='disponibilidad',
        ),
        migrations.RemoveField(
            model_name='mecanico',
            name='turno',
        ),
        migrations.AddField(
            model_name='mecanico',
            name='contrasena',
            field=models.CharField(default='default_password', max_length=20),
        ),
    ]
