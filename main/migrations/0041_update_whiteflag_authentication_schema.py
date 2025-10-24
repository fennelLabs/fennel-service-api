# Generated manually on 2025-10-20
# Migration to support multiple authentications per user and add ECDH public key storage

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("main", "0040_whiteflagauthentication"),
    ]

    operations = [
        # Step 1: Add ecdh_public_key field
        migrations.AddField(
            model_name="whiteflagauthentication",
            name="ecdh_public_key",
            field=models.CharField(
                blank=True,
                help_text="Curve25519 public key (64 hex chars) if using ECDH for Method 2",
                max_length=128,
                null=True,
            ),
        ),
        
        # Step 2: Remove the unique constraint from the user field
        # This is done by converting OneToOneField to ForeignKey
        migrations.AlterField(
            model_name="whiteflagauthentication",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="whiteflag_authentications",  # Changed from singular to plural
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        
        # Step 3: Update verification_data help text for clarity
        migrations.AlterField(
            model_name="whiteflagauthentication",
            name="verification_data",
            field=models.CharField(
                help_text="URL for Method 1, or HKDF-derived token for Method 2",
                max_length=4096,
            ),
        ),
        
        # Step 4: Add ordering to Meta
        migrations.AlterModelOptions(
            name="whiteflagauthentication",
            options={
                "ordering": ["-timestamp"],
                "verbose_name": "Whiteflag Authentication",
                "verbose_name_plural": "Whiteflag Authentications",
            },
        ),
    ]
