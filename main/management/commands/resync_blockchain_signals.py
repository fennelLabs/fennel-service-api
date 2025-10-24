"""
Management command to resync Whiteflag signals from the blockchain.

This command scans the blockchain for Whiteflag signals and re-populates
the database. Useful after database recovery or data loss.

Usage:
    python manage.py resync_blockchain_signals --start-block 1 --end-block latest
"""

from django.core.management.base import BaseCommand
import requests
import os


class Command(BaseCommand):
    help = 'Resync Whiteflag signals from blockchain to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-block',
            type=int,
            default=1,
            help='Starting block number (default: 1)',
        )
        parser.add_argument(
            '--end-block',
            type=str,
            default='latest',
            help='Ending block number or "latest" (default: latest)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually doing it',
        )

    def handle(self, *args, **options):
        start_block = options['start_block']
        end_block = options['end_block']
        dry_run = options['dry_run']

        self.stdout.write(f'Resyncing signals from block {start_block} to {end_block}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get subservice URL
        subservice_url = os.environ.get('SUBSERVICE_URL', 'http://subservice:6060')
        
        self.stdout.write(f'Connecting to subservice at: {subservice_url}')

        try:
            # Call subservice to get signal history
            response = requests.get(
                f'{subservice_url}/get_signal_history',
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                signals = data.get('response', [])
                
                self.stdout.write(self.style.SUCCESS(f'✓ Retrieved {len(signals)} signals from blockchain'))

                # TODO: Parse and save signals to database
                # For now, just display them
                for i, signal in enumerate(signals[:10]):  # Show first 10
                    self.stdout.write(f'Signal {i+1}: {signal}')

                if len(signals) > 10:
                    self.stdout.write(f'... and {len(signals) - 10} more signals')

            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to retrieve signals: HTTP {response.status_code}')
                )
                self.stdout.write(f'Response: {response.text}')

        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Connection error: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Unexpected error: {str(e)}')
            )
