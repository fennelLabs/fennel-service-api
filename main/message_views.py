from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.models import PrivateMessage


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_messages(request):
    return Response(
        [
            {
                "sender": message.sender.username,
                "receiver": message.receiver.username,
                "message": message.message,
                "timestamp": message.timestamp,
                "read": message.read,
            }
            for message in PrivateMessage.objects.filter(receiver=request.user)
        ]
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_sent_messages(request):
    return Response(
        [
            {
                "sender": message.sender.username,
                "receiver": message.receiver.username,
                "message": message.message,
                "timestamp": message.timestamp,
                "read": message.read,
            }
            for message in PrivateMessage.objects.filter(sender=request.user)
        ]
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_message_by_id(_, message_id):
    message = PrivateMessage.objects.get(id=message_id)
    return Response(
        {
            "sender": message.sender.username,
            "receiver": message.receiver.username,
            "message": message.message,
            "timestamp": message.timestamp,
            "read": message.read,
        }
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def send_message(request):
    PrivateMessage.objects.create(
        sender=request.user,
        receiver=request.data["receiver"],
        message=request.data["message"],
    )
    return Response({"success": "message sent"})
