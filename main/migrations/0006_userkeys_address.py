# Generated by Django 4.0.8 on 2023-06-28 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0005_userkeys"),
    ]

    operations = [
        migrations.AddField(
            model_name="userkeys",
            name="address",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
