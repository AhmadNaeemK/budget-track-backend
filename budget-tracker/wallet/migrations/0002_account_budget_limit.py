# Generated by Django 3.2.6 on 2021-09-08 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='budget_limit',
            field=models.FloatField(default=0),
        ),
    ]
