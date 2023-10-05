from silk.profiling.profiler import silk_profile

from main.serializers import (
    ConfirmationRecordSerializer,
    UserSerializer,
)

from main.models import ConfirmationRecord, Signal
from main.whiteflag_helpers import decode


@silk_profile(name="process_decoding_signal")
def process_decoding_signal(user, signal):
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
    references = [
        process_decoding_signal(user, reference_signal)
        for reference_signal in signal.references.filter(
            signal_text__startswith="574631"
        )
    ]
    return {
        "id": signal.id,
        "tx_hash": signal.tx_hash,
        "timestamp": signal.timestamp,
        "mempool_timestamp": signal.mempool_timestamp,
        "signal_text": signal_body if success else signal.signal_text,
        "sender": UserSerializer(signal.sender).data,
        "synced": signal.synced,
        "references": references,
        "confirmations": ConfirmationRecordSerializer(
            ConfirmationRecord.objects.filter(signal=signal), many=True
        ).data,
        "decoded": success,
        "error": signal_body["error"] if not success else None,
    }
