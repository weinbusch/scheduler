# Generated by Django 4.0.6 on 2022-07-20 06:25

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('solver', '0009_schedule_users'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='daypreference',
            name='available',
        ),
        migrations.AlterField(
            model_name='schedule',
            name='users',
            field=models.ManyToManyField(blank=True, related_name='schedules', to=settings.AUTH_USER_MODEL),
        ),
    ]
