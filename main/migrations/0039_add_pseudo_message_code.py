# Generated manually for test message support
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0038_add_blockchain_indexing_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='signal',
            name='pseudo_message_code',
            field=models.CharField(
                blank=True,
                help_text='For test messages (T), stores the original message code being tested',
                max_length=2,
                null=True
            ),
        ),
    ]
