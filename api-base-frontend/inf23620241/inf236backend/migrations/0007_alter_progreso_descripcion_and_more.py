# Generated by Django 4.2.11 on 2024-06-06 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inf236backend', '0006_jefemotores'),
    ]

    operations = [
        migrations.AlterField(
            model_name='progreso',
            name='descripcion',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='progreso',
            name='fecha_progreso',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
