# Generated by Django 3.2.9 on 2021-11-18 05:42

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='transaction_time',
            field=models.DateTimeField(default=datetime.datetime(2021, 11, 18, 5, 42, 1, 892384, tzinfo=utc)),
        ),
    ]
