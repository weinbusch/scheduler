# Generated by Django 4.0.6 on 2022-08-23 20:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('solver', '0018_assignment_unique_assignment'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='owner',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='my_schedules', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
