# Generated by Django 4.1.10 on 2023-09-20 01:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0032_apigroupjoinrequest_rejected"),
    ]

    operations = [
        migrations.AddField(
            model_name="signal",
            name="viewers",
            field=models.ManyToManyField(
                blank=True, related_name="viewable_signals", to="main.apigroup"
            ),
        ),
    ]
