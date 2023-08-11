# Generated by Django 4.1.10 on 2023-08-11 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0023_userkeys_blockchain_public_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="apigroup",
            name="email",
            field=models.EmailField(
                default="info@fennellabs.com",
                max_length=1024,
            ),
            preserve_default=False,
        ),
    ]