# Generated by Django 4.1.10 on 2023-07-12 18:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0010_signal_confirmed_timestamp_confirmationrecord"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="signal",
            name="confirmed_timestamp",
        ),
    ]
