from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from main.models import APIGroup, ConfirmationRecord, Signal, Transaction, UserKeys


class UserKeysSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserKeys
        fields = (
            "id",
            "address",
            "blockchain_public_key",
            "balance",
            "public_diffie_hellman_key",
        )


class UserSerializer(serializers.ModelSerializer):
    keys = UserKeysSerializer(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "keys")


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            validated_data["username"],
            validated_data["email"],
            validated_data["password"],
        )
        return user


# pylint: disable=W0223
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=False
    )

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"), username=username, password=password
        )

        if not user:
            msg = "Unable to authenticate with provided credentials"
            raise serializers.ValidationError(msg, code="authentication")

        return user


# pylint: disable=W0223
class ChangePasswordSerializer(serializers.Serializer):
    model = User

    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    # pylint: disable=R0201
    def validate_new_password(self, value):
        validate_password(value)
        return value


class CustomTokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"


class ConfirmationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfirmationRecord
        fields = "__all__"


class SignalSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    confirmations = ConfirmationRecordSerializer(many=True, read_only=True)

    class Meta:
        model = Signal
        fields = [
            "id",
            "tx_hash",
            "signal_text",
            "timestamp",
            "mempool_timestamp",
            "sender",
            "synced",
            "references",
            "confirmations",
        ]


class APIGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIGroup
        fields = "__all__"


class APIGroupJoinRequestSerializer(serializers.Serializer):
    api_group = APIGroupSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = APIGroup
        fields = "__all__"


class AnnotatedWhiteflagSignalSerializer(serializers.Serializer):
    signal_body = serializers.JSONField()
    annotations = serializers.JSONField()
    recipient_group = serializers.CharField(required=False)


class SignalTextSerializer(serializers.Serializer):
    signals = serializers.ListField(child=serializers.CharField())


class EncodeListSerializer(serializers.Serializer):
    signals = serializers.ListField(child=serializers.JSONField())
    recipient_group = serializers.CharField(required=False)


class DecodeListSerializer(serializers.Serializer):
    signals = serializers.ListField(child=serializers.IntegerField())
