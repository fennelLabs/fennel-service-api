# Generated by Django 4.1.10 on 2023-09-04 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0026_alter_transaction_fee"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userkeys",
            name="balance",
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
