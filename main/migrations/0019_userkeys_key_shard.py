# Generated by Django 4.1.10 on 2023-08-05 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0018_apigroup"),
    ]

    operations = [
        migrations.AddField(
            model_name="userkeys",
            name="key_shard",
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]