# Generated by Django 5.0.6 on 2024-06-06 06:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0027_alter_manage_equiment_stud_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='manage_equiment',
            old_name='date',
            new_name='borrowed_date',
        ),
    ]