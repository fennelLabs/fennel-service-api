"""
WhiteFlag Explorer Views
Public, read-only API endpoints for exploring WhiteFlag messages
"""
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import AnonRateThrottle
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

# Import models from main app
from main.models import Signal, User


# WhiteFlag Protocol Decoders
MESSAGE_CODES = {
    'A': 'Authentication',
    'K': 'Cryptographic',
    'T': 'Test',
    'Q': 'Request',
    'P': 'Protective Sign',
    'E': 'Emergency Signal',
    'D': 'Danger',
    'S': 'Status',
    'I': 'Infrastructure',
    'M': 'Mission',
    'R': 'Resource',
    'F': 'Free Text',
}

SUBJECT_CODES = {
    # Infrastructure subject codes (I message)
    '01': 'Multiple Types',
    '10': 'Medical',
    '11': 'Food Distribution',
    '12': 'Water Distribution',
    '20': 'Utilities',
    '21': 'Electricity Network',
    '22': 'Gas Network',
    '23': 'Water Network',
    '24': 'Heating Network',
    '25': 'Sewage Network',
    '26': 'Telecommunications',
    '30': 'Transport',
    '31': 'Road Transport',
    '32': 'Railway Transport',
    '33': 'Water Transport',
    '34': 'Air Transport',
    '40': 'Police',
    '41': 'Fire Fighting',
    '42': 'Emergency Medical',
    '43': 'Rescue',
    '44': 'Safety',
    '50': 'Military',
    '51': 'Government',
    '52': 'Public Service - School',
    '53': 'Financial',
    '54': 'Religious',
    '60': 'Agriculture',
    '61': 'Mining',
    '62': 'Manufacturing',
    '63': 'Construction',
    '64': 'Trade',
    '65': 'Accommodation',
    '66': 'Information Service',
    '67': 'Professional Service',
    '68': 'Administrative Service',
    '70': 'Entertainment',
    '71': 'Nature',
    '72': 'Historical',
    '73': 'Archeological',
}


def decode_subject_code(subject_code):
    """Decode WhiteFlag subject code to human-readable string"""
    if not subject_code:
        return None
    return SUBJECT_CODES.get(subject_code, f"Unknown ({subject_code})")


def decode_message_code(message_code):
    """Decode WhiteFlag message code to human-readable string"""
    if not message_code:
        return None
    return MESSAGE_CODES.get(message_code, f"Unknown ({message_code})")


class ExplorerPagination(PageNumberPagination):
    """Pagination for explorer endpoints"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class ExplorerRateThrottle(AnonRateThrottle):
    """Rate limiting for public explorer endpoints"""
    rate = '100/hour'  # 100 requests per hour per IP


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([ExplorerRateThrottle])
def messages_list(request):
    """
    List all finalized WhiteFlag messages (public, read-only)
    
    Query parameters:
    - sender: Filter by username
    - message_code: Filter by message type (A, P, E, I, etc.)
    - finalized: Filter by on-chain status (default: true, shows messages with block numbers)
    - q: Search query (searches signal_body, subject_code, sender)
    - page: Page number (default: 1)
    - page_size: Results per page (default: 50, max: 100)
    """
    
    # Filter parameters
    sender = request.GET.get('sender')
    message_code = request.GET.get('message_code')
    finalized = request.GET.get('finalized', 'true').lower() == 'true'
    search = request.GET.get('q')
    
    # Base queryset - default to messages that are on-chain (have block numbers)
    if finalized:
        queryset = Signal.objects.filter(block_number__isnull=False)
    else:
        queryset = Signal.objects.all()
    
    queryset = queryset.select_related('sender').order_by('-timestamp')
    
    # Apply filters
    if sender:
        queryset = queryset.filter(sender__username=sender)
    if message_code:
        queryset = queryset.filter(message_code=message_code)
    if search:
        queryset = queryset.filter(
            Q(signal_body__icontains=search) |
            Q(subject_code__icontains=search) |
            Q(sender__username__icontains=search)
        )
    
    # Paginate
    paginator = ExplorerPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    # Serialize (exclude sensitive fields)
    data = [{
        'id': signal.id,
        'tx_hash': signal.tx_hash,
        'message_code': signal.message_code,
        'message_type': decode_message_code(signal.message_code),
        'subject_code': signal.subject_code,
        'subject_type': decode_subject_code(signal.subject_code),
        'signal_body': signal.signal_body,
        'block_number': signal.block_number,
        'block_hash': signal.block_hash,
        'sender': signal.sender.username if signal.sender else None,
        'created_at': signal.timestamp.isoformat(),
        'finalized': signal.finalized,
        'reference_count': signal.references.count() if hasattr(signal, 'references') else 0,
    } for signal in page]
    
    return paginator.get_paginated_response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([ExplorerRateThrottle])
def message_detail(request, message_id):
    """
    Get detailed information about a specific message
    
    Path parameters:
    - message_id: Signal ID
    """
    try:
        # Accept any message with a block number (on-chain = finalized)
        signal = Signal.objects.select_related('sender').get(
            id=message_id, 
            block_number__isnull=False
        )
    except Signal.DoesNotExist:
        return Response({'error': 'Message not found or not on-chain'}, status=404)
    
    # Get references and referenced_by
    references = []
    if hasattr(signal, 'references'):
        references = [ref.id for ref in signal.references.all()]
    
    referenced_by = Signal.objects.filter(references=signal).values_list('id', flat=True)
    
    return Response({
        'id': signal.id,
        'tx_hash': signal.tx_hash,
        'message_code': signal.message_code,
        'message_type': decode_message_code(signal.message_code),
        'subject_code': signal.subject_code,
        'subject_type': decode_subject_code(signal.subject_code),
        'signal_body': signal.signal_body,
        'block_number': signal.block_number,
        'block_hash': signal.block_hash,
        'extrinsic_index': signal.extrinsic_index,
        'sender': {
            'username': signal.sender.username if signal.sender else None,
            'message_count': Signal.objects.filter(sender=signal.sender, block_number__isnull=False).count() if signal.sender else 0
        },
        'created_at': signal.timestamp.isoformat(),
        'finalized': signal.finalized,
        'references': list(references),
        'referenced_by': list(referenced_by),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([ExplorerRateThrottle])
def account_profile(request, username):
    """
    Get public profile for a WhiteFlag account
    
    Path parameters:
    - username: WhiteFlag account username
    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'Account not found'}, status=404)
    
    # Only show messages that are on-chain (have block numbers)
    signals = Signal.objects.filter(sender=user, block_number__isnull=False)
    
    # Message type breakdown
    message_types = list(signals.values('message_code').annotate(count=Count('id')))
    
    # First and last message dates
    first_signal = signals.order_by('timestamp').first()
    last_signal = signals.order_by('-timestamp').first()
    
    return Response({
        'username': user.username,
        'message_count': signals.count(),
        'message_types': message_types,
        'first_message': first_signal.timestamp.isoformat() if first_signal else None,
        'last_message': last_signal.timestamp.isoformat() if last_signal else None,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([ExplorerRateThrottle])
def network_stats(request):
    """
    Get overall WhiteFlag network statistics
    """
    # Only count messages that are on-chain (have block numbers)
    signals = Signal.objects.filter(block_number__isnull=False)
    
    # Recent activity
    now = timezone.now()
    recent_24h = signals.filter(timestamp__gte=now - timedelta(days=1)).count()
    recent_7d = signals.filter(timestamp__gte=now - timedelta(days=7)).count()
    recent_30d = signals.filter(timestamp__gte=now - timedelta(days=30)).count()
    
    # Message type breakdown
    message_types = list(signals.values('message_code').annotate(count=Count('id')))
    
    # Active senders
    active_senders = signals.values('sender').distinct().count()
    
    return Response({
        'total_messages': signals.count(),
        'message_types': message_types,
        'active_senders': active_senders,
        'recent_activity': {
            '24h': recent_24h,
            '7d': recent_7d,
            '30d': recent_30d,
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([ExplorerRateThrottle])
def search_messages(request):
    """
    Full-text search across WhiteFlag messages
    
    Query parameters:
    - q: Search query (required)
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        return Response({'error': 'Search query required (parameter: q)'}, status=400)
    
    if len(query) < 3:
        return Response({'error': 'Search query must be at least 3 characters'}, status=400)
    
    # Search across multiple fields (only on-chain messages)
    results = Signal.objects.filter(
        Q(signal_body__icontains=query) |
        Q(subject_code__icontains=query) |
        Q(sender__username__icontains=query),
        block_number__isnull=False
    ).select_related('sender').order_by('-timestamp')[:50]
    
    return Response([{
        'id': signal.id,
        'message_code': signal.message_code,
        'signal_body': signal.signal_body[:200] + '...' if len(signal.signal_body) > 200 else signal.signal_body,
        'sender': signal.sender.username if signal.sender else None,
        'created_at': signal.timestamp.isoformat(),
        'block_number': signal.block_number,
    } for signal in results])


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([ExplorerRateThrottle])
def reference_graph(request, message_id):
    """
    Get the reference graph for a message (what it references and what references it)
    
    Path parameters:
    - message_id: Signal ID
    """
    try:
        # Only show messages that are on-chain
        signal = Signal.objects.get(id=message_id, block_number__isnull=False)
    except Signal.DoesNotExist:
        return Response({'error': 'Message not found or not on-chain'}, status=404)
    
    # Messages this one references
    references = []
    if hasattr(signal, 'references'):
        references = [{
            'id': ref.id,
            'message_code': ref.message_code,
            'sender': ref.sender.username if ref.sender else None,
            'created_at': ref.timestamp.isoformat(),
        } for ref in signal.references.all()]
    
    # Messages that reference this one (only on-chain)
    referenced_by = Signal.objects.filter(
        references=signal, 
        block_number__isnull=False
    ).select_related('sender')
    
    referenced_by_data = [{
        'id': s.id,
        'message_code': s.message_code,
        'sender': s.sender.username if s.sender else None,
        'created_at': s.timestamp.isoformat(),
    } for s in referenced_by]
    
    return Response({
        'message': {
            'id': signal.id,
            'message_code': signal.message_code,
            'sender': signal.sender.username if signal.sender else None,
        },
        'references': references,
        'referenced_by': referenced_by_data,
    })
