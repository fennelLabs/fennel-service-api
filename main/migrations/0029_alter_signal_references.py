# Generated by Django 4.1.10 on 2023-09-11 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0028_signal_references"),
    ]

    operations = [
        migrations.AlterField(
            model_name="signal",
            name="references",
            field=models.ManyToManyField(to="main.signal"),
        ),
    ]
