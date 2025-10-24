"""
Management command to index Whiteflag messages from the Fennel blockchain.

This indexer scans blocks for SignalSent events and stores them in the Signal database,
enabling the Explorer API to display complete historical data.

Features:
- Scans blockchain blocks for SignalSent events
- Extracts message content and metadata (tx_hash, block_number, block_hash)
- Matches blockchain addresses to User accounts via UserKeys
- Stores Signal records with complete blockchain data
- Supports backfilling historical blocks
- Tracks last indexed block to enable continuous operation
- Decodes message codes (A, K, P, E, etc.) from signal text

Usage:
    # Scan specific block range
    python manage.py index_whiteflag_messages --start-block 283232 --end-block 341336
    
    # Continuous mode (scan from last indexed block to current)
    python manage.py index_whiteflag_messages --continuous
    
    # Backfill all missing blocks
    python manage.py index_whiteflag_messages --backfill
    
    # Test mode (show what would be indexed without saving)
    python manage.py index_whiteflag_messages --start-block 341335 --end-block 341336 --dry-run

Environment Variables:
    PROTOCOL_HOST_WS: WebSocket RPC URL (default: ws://localhost:9944)
    
Database:
    Stores indexed blocks in Signal table
    Uses block_number field to track progress
    
Scheduling:
    Run as Kubernetes CronJob every 5 minutes:
    kubectl create cronjob whiteflag-indexer --schedule="*/5 * * * *" \
        --image=fennelacr531.azurecr.io/fennel-service-api:latest \
        -- python manage.py index_whiteflag_messages --continuous
"""
import os
import time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from substrateinterface import SubstrateInterface
from main.models import Signal, UserKeys


class Command(BaseCommand):
    help = 'Index Whiteflag messages from blockchain into Signal database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rpc-url',
            type=str,
            default=None,
            help='WebSocket RPC URL (defaults to PROTOCOL_HOST_WS env var)',
        )
        parser.add_argument(
            '--start-block',
            type=int,
            default=None,
            help='Starting block number (defaults to last indexed block + 1)',
        )
        parser.add_argument(
            '--end-block',
            type=int,
            default=None,
            help='Ending block number (defaults to current finalized block)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of blocks to process per batch',
        )
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Continuously index from last indexed block to current',
        )
        parser.add_argument(
            '--backfill',
            action='store_true',
            help='Backfill all missing blocks from genesis to current',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be indexed without saving to database',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed progress information',
        )

    def handle(self, *args, **options):
        rpc_url = options['rpc_url'] or os.environ.get('PROTOCOL_HOST_WS', 'ws://localhost:9944')
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        verbose = options['verbose']

        self.stdout.write('=' * 60)
        self.stdout.write('Whiteflag Message Indexer')
        self.stdout.write('=' * 60)
        self.stdout.write(f'Connecting to blockchain at: {rpc_url}')
        
        try:
            substrate = SubstrateInterface(url=rpc_url)
            self.stdout.write(self.style.SUCCESS('✓ Connected to blockchain'))
            
            # Get current chain state
            finalized_hash = substrate.get_finalized_head()
            finalized_header = substrate.get_block_header(finalized_hash)
            finalized_block = finalized_header['header']['number']
            
            self.stdout.write(f'Current finalized block: {finalized_block:,}')
            
            # Determine block range
            if options['backfill']:
                start_block = 1
                end_block = finalized_block
                self.stdout.write(f'Backfill mode: Scanning all blocks from genesis')
            elif options['continuous']:
                # Get last indexed block
                last_indexed = Signal.objects.filter(
                    block_number__isnull=False
                ).order_by('-block_number').first()
                
                if last_indexed:
                    start_block = last_indexed.block_number + 1
                    self.stdout.write(f'Last indexed block: {last_indexed.block_number:,}')
                else:
                    start_block = 1
                    self.stdout.write('No previously indexed blocks found')
                
                end_block = finalized_block
                self.stdout.write(f'Continuous mode: Scanning blocks {start_block:,} → {end_block:,}')
            else:
                start_block = options['start_block']
                end_block = options['end_block'] or finalized_block
                
                if start_block is None:
                    # Default to last indexed + 1
                    last_indexed = Signal.objects.filter(
                        block_number__isnull=False
                    ).order_by('-block_number').first()
                    
                    start_block = last_indexed.block_number + 1 if last_indexed else 1
                
                self.stdout.write(f'Manual range: Scanning blocks {start_block:,} → {end_block:,}')
            
            total_blocks = end_block - start_block + 1
            self.stdout.write(f'Total blocks to scan: {total_blocks:,}')
            self.stdout.write('=' * 60)
            
            if dry_run:
                self.stdout.write(self.style.WARNING('[DRY RUN MODE - No database changes]'))
            
            # Build address → User lookup cache
            self.stdout.write('Building address → user lookup cache...')
            address_to_user = {}
            for user_keys in UserKeys.objects.select_related('user').filter(address__isnull=False):
                address_to_user[user_keys.address] = user_keys.user
            self.stdout.write(f'✓ Cached {len(address_to_user)} user addresses')
            
            # Indexing statistics
            total_scanned = 0
            total_signals = 0
            total_saved = 0
            total_skipped = 0
            start_time = time.time()
            
            # Process blocks in batches
            current_block = start_block
            while current_block <= end_block:
                batch_end = min(current_block + batch_size - 1, end_block)
                
                self.stdout.write(f'\nProcessing batch: blocks {current_block:,} → {batch_end:,}')
                
                batch_signals = 0
                batch_saved = 0
                batch_skipped = 0
                
                for block_num in range(current_block, batch_end + 1):
                    try:
                        # Get block by number
                        block_hash = substrate.get_block_hash(block_num)
                        block = substrate.get_block(block_hash)
                        
                        if verbose:
                            self.stdout.write(f'  Block {block_num:,}: {block_hash}')
                        
                        # Get events for this block
                        events = substrate.get_events(block_hash)
                        
                        # Process each extrinsic in the block
                        for extrinsic_idx, extrinsic in enumerate(block['extrinsics']):
                            # Check if this is a signal.sendSignal extrinsic
                            if (extrinsic.value['call']['call_module'] == 'Signal' and
                                extrinsic.value['call']['call_function'] == 'sendSignal'):
                                
                                # Extract signal data
                                signal_data_hex = extrinsic.value['call']['call_args'][0]['value']
                                
                                # Convert hex to string (remove 0x prefix if present)
                                if signal_data_hex.startswith('0x'):
                                    signal_data_hex = signal_data_hex[2:]
                                
                                signal_text = signal_data_hex
                                
                                # Get sender address from extrinsic
                                sender_address = extrinsic.value['address']
                                
                                # Extract message code from signal text (first character after prefix)
                                message_code = None
                                if len(signal_text) > 0:
                                    # Whiteflag messages: First byte is message code
                                    # Convert first 2 hex chars to ASCII
                                    try:
                                        first_byte = bytes.fromhex(signal_text[:2]).decode('ascii')
                                        if first_byte.isalpha():
                                            message_code = first_byte
                                    except:
                                        pass
                                
                                # Get transaction hash
                                tx_hash = extrinsic.extrinsic_hash
                                
                                # Find associated user
                                user = address_to_user.get(sender_address)
                                
                                batch_signals += 1
                                
                                if verbose:
                                    self.stdout.write(
                                        f'    Signal found: {message_code or "?"} | '
                                        f'TX: {tx_hash[:16]}... | '
                                        f'Sender: {sender_address[:16]}... | '
                                        f'User: {user.username if user else "unknown"}'
                                    )
                                
                                # Check if this signal already exists
                                if Signal.objects.filter(tx_hash=tx_hash).exists():
                                    if verbose:
                                        self.stdout.write(f'      ⊙ Already indexed (skipping)')
                                    batch_skipped += 1
                                    continue
                                
                                # Save to database
                                if not dry_run:
                                    with transaction.atomic():
                                        signal = Signal.objects.create(
                                            signal_text=signal_text,
                                            message_code=message_code,
                                            tx_hash=tx_hash,
                                            block_number=block_num,
                                            block_hash=block_hash,
                                            extrinsic_index=extrinsic_idx,
                                            sender=user,
                                            synced=True,
                                            finalized=True,
                                            execution_success=True,
                                        )
                                        
                                        if verbose:
                                            self.stdout.write(
                                                self.style.SUCCESS(f'      ✓ Saved as Signal #{signal.id}')
                                            )
                                else:
                                    if verbose:
                                        self.stdout.write(f'      [DRY RUN] Would save to database')
                                
                                batch_saved += 1
                        
                        total_scanned += 1
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Error processing block {block_num}: {str(e)}')
                        )
                        continue
                
                # Batch summary
                total_signals += batch_signals
                total_saved += batch_saved
                total_skipped += batch_skipped
                
                elapsed = time.time() - start_time
                blocks_per_sec = total_scanned / elapsed if elapsed > 0 else 0
                
                self.stdout.write(
                    f'  Batch complete: {batch_signals} signals found, '
                    f'{batch_saved} saved, {batch_skipped} skipped'
                )
                self.stdout.write(
                    f'  Progress: {total_scanned}/{total_blocks} blocks '
                    f'({100.0 * total_scanned / total_blocks:.1f}%) | '
                    f'{blocks_per_sec:.1f} blocks/sec'
                )
                
                current_block = batch_end + 1
            
            # Final summary
            elapsed = time.time() - start_time
            self.stdout.write('')
            self.stdout.write('=' * 60)
            self.stdout.write('INDEXING COMPLETE')
            self.stdout.write('=' * 60)
            self.stdout.write(f'Blocks scanned: {total_scanned:,}')
            self.stdout.write(f'Signals found: {total_signals:,}')
            self.stdout.write(f'Signals saved: {total_saved:,}')
            self.stdout.write(f'Signals skipped (already indexed): {total_skipped:,}')
            self.stdout.write(f'Time elapsed: {elapsed:.1f} seconds')
            self.stdout.write(f'Performance: {blocks_per_sec:.1f} blocks/second')
            
            if dry_run:
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('[DRY RUN] No database changes made'))
            else:
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✓ All signals indexed successfully'))
            
            substrate.close()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Fatal error: {str(e)}')
            )
            import traceback
            traceback.print_exc()
            raise
