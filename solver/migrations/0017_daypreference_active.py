# Generated by Django 4.0.6 on 2022-07-30 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solver', '0016_alter_schedule_end_alter_schedule_start'),
    ]

    operations = [
        migrations.AddField(
            model_name='daypreference',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]