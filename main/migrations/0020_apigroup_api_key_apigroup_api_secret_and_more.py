# Generated by Django 4.1.10 on 2023-08-06 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0019_userkeys_key_shard"),
    ]

    operations = [
        migrations.AddField(
            model_name="apigroup",
            name="api_key",
            field=models.CharField(blank=True, max_length=1024, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="apigroup",
            name="api_secret",
            field=models.CharField(blank=True, max_length=1024, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="apigroup",
            name="request_counter",
            field=models.IntegerField(default=0),
        ),
    ]
