# Generated by Django 4.0.6 on 2022-08-14 18:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solver', '0017_daypreference_active'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='assignment',
            constraint=models.UniqueConstraint(fields=('start', 'schedule'), name='unique_assignment'),
        ),
    ]
