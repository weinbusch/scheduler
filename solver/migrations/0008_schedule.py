# Generated by Django 4.0.6 on 2022-07-12 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solver', '0007_remove_userpreferences_friday_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateField()),
                ('end', models.DateField()),
            ],
        ),
    ]