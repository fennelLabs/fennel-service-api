# Generated by Django 4.0.8 on 2023-06-28 20:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0007_userkeys_balance"),
    ]

    operations = [
        migrations.AddField(
            model_name="signal",
            name="mempool_timestamp",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
