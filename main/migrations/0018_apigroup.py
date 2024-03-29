# Generated by Django 4.1.10 on 2023-08-04 13:31

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("main", "0017_alter_signal_signal_text_alter_signal_tx_hash_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="APIGroup",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=1024, unique=True)),
                ("active", models.BooleanField(default=True)),
                (
                    "admin_list",
                    models.ManyToManyField(
                        related_name="api_group_admins", to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "user_list",
                    models.ManyToManyField(
                        related_name="api_group_users", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
        ),
    ]
