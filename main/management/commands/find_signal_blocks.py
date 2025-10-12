"""
Management command to find block numbers for signals.

Usage examples:
  # Find block for specific signal ID
  python manage.py find_signal_blocks --id 65

  # Find blocks for date range
  python manage.py find_signal_blocks --start-date 2025-09-25 --end-date 2025-09-26

  # Find blocks by transaction hash
  python manage.py find_signal_blocks --tx-hash 0xdbd97e3445ec77a9...

  # Find all signals in block range
  python manage.py find_signal_blocks --start-block 249000 --end-block 250000

  # Export to CSV
  python manage.py find_signal_blocks --start-date 2025-09-25 --end-date 2025-09-26 --csv output.csv
"""

from django.core.management.base import BaseCommand
from main.models import Signal
import csv


class Command(BaseCommand):
    help = 'Find block numbers for Whiteflag signals'

    def add_arguments(self, parser):
        # Query by signal ID
        parser.add_argument(
            '--id',
            type=int,
            help='Signal ID to look up'
        )

        # Query by transaction hash
        parser.add_argument(
            '--tx-hash',
            type=str,
            help='Transaction hash to look up'
        )

        # Query by date range
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date (YYYY-MM-DD)'
        )

        # Query by block range
        parser.add_argument(
            '--start-block',
            type=int,
            help='Start block number'
        )
        parser.add_argument(
            '--end-block',
            type=int,
            help='End block number'
        )

        # Output format
        parser.add_argument(
            '--csv',
            type=str,
            help='Export results to CSV file'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output as JSON'
        )

    def filter_signals(self, signals, options):
        """Apply filters to signal queryset based on command options."""
        # Filter by ID
        if options['id']:
            signals = signals.filter(id=options['id'])

        # Filter by transaction hash
        if options['tx_hash']:
            signals = signals.filter(tx_hash=options['tx_hash'])

        # Filter by date range
        if options['start_date']:
            signals = signals.filter(timestamp__gte=options['start_date'])
        if options['end_date']:
            # Add one day to include the end date
            from datetime import datetime, timedelta
            end_date = datetime.strptime(options['end_date'], '%Y-%m-%d') + timedelta(days=1)
            signals = signals.filter(timestamp__lt=end_date)

        # Filter by block range
        if options['start_block']:
            signals = signals.filter(block_number__gte=options['start_block'])
        if options['end_block']:
            signals = signals.filter(block_number__lte=options['end_block'])

        # Only show signals with block numbers
        signals = signals.filter(block_number__isnull=False)

        # Order by block number
        return signals.order_by('block_number')

    def output_json(self, signals):
        """Output signals in JSON format."""
        import json
        output = []
        for signal in signals:
            output.append({
                'id': signal.id,
                'block_number': signal.block_number,
                'block_hash': signal.block_hash,
                'tx_hash': signal.tx_hash,
                'extrinsic_index': signal.extrinsic_index,
                'execution_success': signal.execution_success,
                'finalized': signal.finalized,
                'timestamp': signal.timestamp.isoformat() if signal.timestamp else None,
                'sender': signal.sender.username if signal.sender else None,
            })
        self.stdout.write(json.dumps(output, indent=2))

    def output_csv(self, signals, filename):
        """Output signals to CSV file."""
        fieldnames = [
            'signal_id', 'block_number', 'block_hash', 'tx_hash',
            'extrinsic_index', 'execution_success', 'finalized',
            'timestamp', 'sender'
        ]

        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for signal in signals:
                writer.writerow({
                    'signal_id': signal.id,
                    'block_number': signal.block_number,
                    'block_hash': signal.block_hash,
                    'tx_hash': signal.tx_hash,
                    'extrinsic_index': signal.extrinsic_index,
                    'execution_success': signal.execution_success,
                    'finalized': signal.finalized,
                    'timestamp': signal.timestamp.isoformat() if signal.timestamp else '',
                    'sender': signal.sender.username if signal.sender else '',
                })

        self.stdout.write(
            self.style.SUCCESS(f'Exported {signals.count()} signals to {filename}')
        )

    def output_table(self, signals):
        """Output signals in table format."""
        self.stdout.write(self.style.SUCCESS(f'\nFound {signals.count()} signals:\n'))
        self.stdout.write('-' * 120)

        # Header
        self.stdout.write(
            f"{'ID':>5} | {'Block':>10} | {'Block Hash':20} | {'TX Hash':20} | "
            f"{'Index':>5} | {'Success':>7} | {'Timestamp':19}"
        )
        self.stdout.write('-' * 120)

        # Data rows
        for signal in signals:
            block_hash_short = signal.block_hash[:18] + '...' if signal.block_hash else 'N/A'
            tx_hash_short = signal.tx_hash[:18] + '...' if signal.tx_hash else 'N/A'
            timestamp_str = signal.timestamp.strftime('%Y-%m-%d %H:%M:%S') if signal.timestamp else 'N/A'

            self.stdout.write(
                f"{signal.id:>5} | {signal.block_number:>10} | {block_hash_short:20} | "
                f"{tx_hash_short:20} | {signal.extrinsic_index:>5} | "
                f"{str(signal.execution_success):>7} | {timestamp_str:19}"
            )

        self.stdout.write('-' * 120)
        self.stdout.write(f'\nTotal: {signals.count()} signals\n')

    def handle(self, *args, **options):
        signals = Signal.objects.all()

        # Apply filters
        signals = self.filter_signals(signals, options)

        # Check if any results
        if not signals.exists():
            self.stdout.write(self.style.WARNING('No signals found matching criteria'))
            return

        # Output format
        if options['json']:
            self.output_json(signals)
        elif options['csv']:
            self.output_csv(signals, options['csv'])
        else:
            self.output_table(signals)
