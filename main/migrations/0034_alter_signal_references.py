# Generated by Django 4.1.10 on 2023-10-03 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0033_signal_viewers"),
    ]

    operations = [
        migrations.AlterField(
            model_name="signal",
            name="references",
            field=models.ManyToManyField(
                blank=True, related_name="referenced_by", to="main.signal"
            ),
        ),
    ]