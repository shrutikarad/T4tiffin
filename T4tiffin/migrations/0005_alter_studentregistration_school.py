# Generated by Django 5.1.3 on 2024-12-24 11:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('T4tiffin', '0004_rename_school_id_studentregistration_school'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentregistration',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='T4tiffin.school'),
        ),
    ]
