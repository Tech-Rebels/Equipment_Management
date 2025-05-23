# Generated by Django 5.0.6 on 2024-11-19 12:59

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UApp', '0018_transaction_treatment_transaction_treatmentname'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='equipment',
            constraint=models.UniqueConstraint(fields=('lab', 'name'), name='unique_equipment_per_lab'),
        ),
    ]
