# Generated by Django 4.0.6 on 2022-07-12 20:25

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('solver', '0008_schedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]
