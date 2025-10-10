"""
Management command to update the finalization status of signals.
This should be run periodically (e.g., every minute) as a background job.

Usage:
    python manage.py update_finalization_status
"""
import os
from django.core.management.base import BaseCommand
from substrateinterface import SubstrateInterface
from main.models import Signal


class Command(BaseCommand):
    help = 'Update finalization status for signals that are included but not finalized'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rpc-url',
            type=str,
            default=None,
            help='WebSocket RPC URL (defaults to PROTOCOL_HOST_WS env var)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of signals to process per batch',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without saving',
        )

    def handle(self, *args, **options):
        rpc_url = options['rpc_url'] or os.environ.get('PROTOCOL_HOST_WS', 'ws://localhost:9944')
        batch_size = options['batch_size']
        dry_run = options['dry_run']

        self.stdout.write(f'Connecting to blockchain at: {rpc_url}')

        try:
            substrate = SubstrateInterface(url=rpc_url)
            self.stdout.write(self.style.SUCCESS('✓ Connected to blockchain'))

            # Get finalized head
            finalized_hash = substrate.get_finalized_head()
            finalized_header = substrate.get_block_header(finalized_hash)
            finalized_number = finalized_header['header']['number']

            self.stdout.write(f'Finalized block: {finalized_number}')

            # Get signals that are included but not finalized
            signals_to_update = Signal.objects.filter(
                block_number__isnull=False,
                finalized=False
            ).order_by('block_number')[:batch_size]

            total_count = signals_to_update.count()
            self.stdout.write(f'Found {total_count} signals to check')

            updated_count = 0
            for signal in signals_to_update:
                if signal.block_number <= finalized_number:
                    if dry_run:
                        self.stdout.write(
                            f'[DRY RUN] Would mark Signal #{signal.id} (block {signal.block_number}) as finalized'
                        )
                    else:
                        signal.finalized = True
                        signal.save(update_fields=['finalized'])
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Signal #{signal.id} (block {signal.block_number}) marked as finalized'
                            )
                        )
                    updated_count += 1
                else:
                    self.stdout.write(
                        f'Signal #{signal.id} (block {signal.block_number}) is not yet finalized'
                    )

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'[DRY RUN] Would have updated {updated_count} signals')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Updated {updated_count} signals to finalized status')
                )

            substrate.close()

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error: {str(e)}')
            )
            raise
