# Generated by Django 4.0.6 on 2022-09-25 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solver', '0025_remove_schedule_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='window',
            field=models.IntegerField(null=True),
        ),
    ]