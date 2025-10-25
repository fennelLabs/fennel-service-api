"""
Management command to monitor Whiteflag messages in real-time via WebSocket.

This monitor uses SubstrateInterface.subscribe_block_headers() to receive push
notifications for new blocks, enabling real-time indexing of Whiteflag messages
with ~6 second latency (block time).

Features:
- Real-time WebSocket subscription to new blocks
- Automatic reconnection on connection loss
- Scans blocks for Signal.send_signal extrinsics
- Stores messages in Signal database
- Deduplicates (checks if tx_hash already exists)
- User matching via UserKeys table

Usage:
    # Run as long-lived process (Kubernetes Deployment)
    python manage.py monitor_whiteflag_messages
    
    # With custom RPC URL
    python manage.py monitor_whiteflag_messages --rpc-url ws://rpc.example.com:9933
    
    # Verbose mode (logs every block)
    python manage.py monitor_whiteflag_messages --verbose
    
    # Finalized blocks only (more reliable, slower)
    python manage.py monitor_whiteflag_messages --finalized-only

Deployment:
    Run as Kubernetes Deployment (not CronJob):
    
    kubectl create deployment whiteflag-monitor \
        --image=fennelacr531.azurecr.io/fennel-service-api:latest \
        --replicas=1 \
        -- python manage.py monitor_whiteflag_messages --verbose

Environment Variables:
    FENNEL_RPC: WebSocket RPC URL (default: ws://localhost:9944)
    PROTOCOL_HOST_WS: Alternative WebSocket RPC URL
    
Architecture:
    This complements the batch indexer (index_whiteflag_messages):
    - WebSocket monitor: Real-time (6s latency)
    - Batch indexer: Safety net (catches missed blocks, runs every 5 min)
"""
import os
import time
import signal
import sys
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction, connection
from substrateinterface import SubstrateInterface
from main.models import Signal, UserKeys


class Command(BaseCommand):
    help = 'Real-time monitor for Whiteflag messages via WebSocket subscription'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rpc-url',
            type=str,
            default=None,
            help='WebSocket RPC URL (defaults to PROTOCOL_HOST_WS env var)',
        )
        parser.add_argument(
            '--finalized-only',
            action='store_true',
            help='Only monitor finalized blocks (more reliable, ~12s delay)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed progress for every block',
        )
        parser.add_argument(
            '--reconnect-delay',
            type=int,
            default=5,
            help='Seconds to wait before reconnecting after error',
        )

    def handle(self, *args, **options):
        rpc_url = options['rpc_url']
        finalized_only = options['finalized_only']
        verbose = options['verbose']
        reconnect_delay = options['reconnect_delay']
        
        # Get RPC URL from env if not provided
        if not rpc_url:
            rpc_url = os.environ.get('PROTOCOL_HOST_WS')
        if not rpc_url:
            rpc_url = os.environ.get('FENNEL_RPC', 'ws://localhost:9944')
        
        self.stdout.write('=' * 70)
        self.stdout.write('WHITEFLAG MESSAGE MONITOR (Real-Time WebSocket)')
        self.stdout.write('=' * 70)
        self.stdout.write(f'RPC URL: {rpc_url}')
        self.stdout.write(f'Mode: {"Finalized blocks only" if finalized_only else "All new blocks"}')
        self.stdout.write(f'Verbose: {verbose}')
        self.stdout.write(f'Reconnect delay: {reconnect_delay}s')
        self.stdout.write('=' * 70)
        self.stdout.write('')
        
        # Handle graceful shutdown
        self.should_stop = False
        
        def signal_handler(signum, frame):
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Shutdown signal received...'))
            self.should_stop = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Monitoring loop with auto-reconnect
        while not self.should_stop:
            try:
                self._run_monitor(rpc_url, finalized_only, verbose)
            except KeyboardInterrupt:
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('Keyboard interrupt...'))
                break
            except Exception as e:
                self.stdout.write('')
                self.stdout.write(self.style.ERROR(f'✗ Monitor error: {str(e)}'))
                
                if self.should_stop:
                    break
                
                self.stdout.write(self.style.WARNING(f'Reconnecting in {reconnect_delay} seconds...'))
                time.sleep(reconnect_delay)
        
        self.stdout.write('')
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.SUCCESS('Monitor stopped'))
        self.stdout.write('=' * 70)

    def _run_monitor(self, rpc_url, finalized_only, verbose):
        """Run the WebSocket monitor (single connection lifecycle)"""
        
        # Connect to blockchain
        self.stdout.write(f'Connecting to {rpc_url}...')
        substrate = SubstrateInterface(url=rpc_url)
        self.stdout.write(self.style.SUCCESS('✓ Connected'))
        
        # Build address-to-user mapping (refresh periodically)
        address_to_user = self._build_user_mapping()
        last_mapping_refresh = time.time()
        mapping_refresh_interval = 300  # Refresh every 5 minutes
        
        # Stats
        total_blocks = 0
        total_messages = 0
        start_time = time.time()
        
        def block_handler(obj, update_nr, subscription_id):
            """
            Called for each new block.
            
            Args:
                obj: Block header data
                update_nr: Number of updates received (0, 1, 2, ...)
                subscription_id: Subscription ID
            
            Returns:
                None to continue, any value to stop
            """
            nonlocal total_blocks, total_messages, address_to_user, last_mapping_refresh
            
            # Check if we should stop
            if self.should_stop:
                return "STOP"
            
            # Refresh user mapping periodically
            if time.time() - last_mapping_refresh > mapping_refresh_interval:
                address_to_user = self._build_user_mapping()
                last_mapping_refresh = time.time()
                if verbose:
                    self.stdout.write(f'  ⟳ Refreshed user mapping ({len(address_to_user)} addresses)')
            
            try:
                block_number = obj['header']['number']
                
                # Get block hash from block number
                block_hash = substrate.get_block_hash(block_number)
                
                if verbose:
                    self.stdout.write(f'[{update_nr}] Block #{block_number}: {block_hash}')
                
                # Get full block data (includes extrinsics)
                block = substrate.get_block(block_hash=block_hash)
                
                if not block or 'extrinsics' not in block:
                    if verbose:
                        self.stdout.write('  ⊙ No extrinsics in block')
                    return None
                
                # Scan extrinsics for Signal.send_signal
                messages_found = 0
                for extrinsic_idx, extrinsic in enumerate(block['extrinsics']):
                    call_module = extrinsic.value.get('call', {}).get('call_module')
                    call_function = extrinsic.value.get('call', {}).get('call_function')
                    
                    if call_module == 'Signal' and call_function == 'send_signal':
                        # Extract signal data
                        call_args = extrinsic.value.get('call', {}).get('call_args', [])
                        if not call_args:
                            continue
                        
                        signal_data = call_args[0].get('value', '')
                        if signal_data.startswith('0x'):
                            signal_data = signal_data[2:]
                        
                        # Get sender and tx hash
                        sender_address = extrinsic.value.get('address')
                        tx_hash = extrinsic.extrinsic_hash
                        
                        # Extract message code (first byte)
                        message_code = None
                        if len(signal_data) >= 2:
                            try:
                                first_byte = bytes.fromhex(signal_data[:2]).decode('ascii', errors='ignore')
                                if first_byte.isalpha():
                                    message_code = first_byte
                            except:
                                pass
                        
                        # Check if already exists (deduplication)
                        if Signal.objects.filter(tx_hash=tx_hash).exists():
                            if verbose:
                                self.stdout.write(
                                    f'  ⊙ Signal already indexed: {message_code or "?"} | {tx_hash[:16]}...'
                                )
                            continue
                        
                        # Find user
                        user = address_to_user.get(sender_address)
                        
                        # Save to database
                        with transaction.atomic():
                            signal_obj = Signal.objects.create(
                                signal_text=signal_data,
                                message_code=message_code,
                                tx_hash=tx_hash,
                                block_number=block_number,
                                block_hash=block_hash,
                                extrinsic_index=extrinsic_idx,
                                sender=user,
                                synced=True,
                                finalized=False,  # New blocks aren't finalized yet
                                execution_success=True,
                            )
                        
                        messages_found += 1
                        total_messages += 1
                        
                        # Log the indexed message
                        user_display = user.username if user else 'unknown'
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Indexed: {message_code or "?"} message | '
                                f'Block {block_number} | '
                                f'TX: {tx_hash[:16]}... | '
                                f'User: {user_display} | '
                                f'Signal #{signal_obj.id}'
                            )
                        )
                
                if messages_found > 0 or verbose:
                    if messages_found > 0:
                        self.stdout.write(f'  Found {messages_found} message(s) in block {block_number}')
                    
                    # Show stats periodically
                    if total_blocks % 100 == 0 and total_blocks > 0:
                        elapsed = time.time() - start_time
                        blocks_per_min = (total_blocks / elapsed) * 60 if elapsed > 0 else 0
                        self.stdout.write('')
                        self.stdout.write(f'Stats: {total_blocks} blocks, {total_messages} messages indexed')
                        self.stdout.write(f'  Rate: {blocks_per_min:.1f} blocks/min, Uptime: {elapsed/60:.1f} min')
                        self.stdout.write('')
                
                total_blocks += 1
                
                # Continue monitoring
                return None
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error processing block: {str(e)}'))
                # Continue despite errors (don't stop subscription)
                return None
        
        # Start subscription
        self.stdout.write('')
        self.stdout.write('Starting real-time block subscription...')
        self.stdout.write('Listening for new blocks (Ctrl+C to stop)')
        self.stdout.write('-' * 70)
        
        try:
            # This blocks until handler returns non-None value
            result = substrate.subscribe_block_headers(
                subscription_handler=block_handler,
                include_author=False,
                finalized_only=finalized_only,
            )
            
            if result != "STOP":
                self.stdout.write('')
                self.stdout.write(f'Subscription ended: {result}')
            
        finally:
            substrate.close()
            self.stdout.write('')
            self.stdout.write('WebSocket connection closed')
            
            # Final stats
            elapsed = time.time() - start_time
            self.stdout.write('')
            self.stdout.write('=' * 70)
            self.stdout.write('SESSION SUMMARY')
            self.stdout.write('=' * 70)
            self.stdout.write(f'Blocks processed: {total_blocks:,}')
            self.stdout.write(f'Messages indexed: {total_messages:,}')
            self.stdout.write(f'Session duration: {elapsed/60:.1f} minutes')
            if total_blocks > 0:
                self.stdout.write(f'Average rate: {(total_blocks/elapsed)*60:.1f} blocks/min')

    def _build_user_mapping(self):
        """Build mapping of blockchain addresses to User objects"""
        address_to_user = {}
        for user_key in UserKeys.objects.select_related('user').all():
            if user_key.address:  # address field in UserKeys model
                address_to_user[user_key.address] = user_key.user
        return address_to_user
