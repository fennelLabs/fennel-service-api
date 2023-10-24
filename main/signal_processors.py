from silk.profiling.profiler import silk_profile

from main.serializers import (
    ConfirmationRecordSerializer,
    UserSerializer,
)

from main.models import ConfirmationRecord, Signal
from main.whiteflag_helpers import decode


@silk_profile(name="process_decoding_signal")
def process_decoding_signal(user, signal, depth=0):
    signal_body, success = decode(
        signal.signal_text,
        signal.sender.api_group_users.first() if signal.sender else None,
        user.api_group_users.first(),
    )
    if success:
        if signal_body.get("referencedMessage", None):
            signal.references.set(
                Signal.objects.filter(
                    tx_hash=signal_body.get("referencedMessage", None)
                )
            )
            signal.save()
    references = (
        [
            process_decoding_signal(user, reference_signal, depth=depth + 1)
            for reference_signal in signal.references.filter(
                signal_text__startswith="574631"
            )
        ]
        if depth < 25
        else []
    )
    sender_group = None
    if signal.sender:
        if signal.sender.api_group_users.first():
            sender_group = signal.sender.api_group_users.first().name
    if signal_body:
        signal.signal_body = signal_body
        signal.save()
    return {
        "id": signal.id,
        "tx_hash": signal.tx_hash,
        "timestamp": signal.timestamp,
        "mempool_timestamp": signal.mempool_timestamp,
        "signal_text": signal.signal_text,
        "signal_body": signal_body if success else None,
        "sender": UserSerializer(signal.sender).data,
        "sender_group": sender_group,
        "synced": signal.synced,
        "references": references,
        "confirmations": ConfirmationRecordSerializer(
            ConfirmationRecord.objects.filter(signal=signal), many=True
        ).data,
        "decoded": success,
        "error": signal_body["error"] if not success else None,
    }
