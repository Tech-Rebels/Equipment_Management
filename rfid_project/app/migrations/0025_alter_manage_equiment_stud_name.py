# Generated by Django 5.0.6 on 2024-06-04 07:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0024_remove_equiment_eq_id_equiment_available_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manage_equiment',
            name='stud_name',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.student'),
        ),
    ]