# Generated by Django 5.0.6 on 2024-06-01 07:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rfidno', models.CharField(max_length=100, unique=True)),
                ('regno', models.CharField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(blank=True, max_length=254, null=True, unique=True)),
                ('phone', models.CharField(blank=True, max_length=10, null=True)),
                ('department', models.CharField(max_length=100, null=True)),
                ('course', models.CharField(max_length=100, null=True)),
                ('year', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True)),
                ('idno', models.CharField(blank=True, max_length=100, null=True)),
                ('count', models.IntegerField()),
                ('available', models.BooleanField(default=True)),
                ('category', models.CharField(blank=True, max_length=100, null=True)),
                ('lab', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('borrowed_at', models.DateTimeField(auto_now_add=True)),
                ('returned_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.BooleanField(default=False)),
                ('equipment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='UApp.equipment')),
                ('handled_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='UApp.student')),
            ],
        ),
    ]