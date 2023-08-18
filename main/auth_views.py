from datetime import timedelta
from typing import Any

from django.contrib.auth.models import User
from django.contrib.auth import login
from django.utils import timezone
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from knox.models import AuthToken

from rest_framework.views import APIView
from rest_framework import parsers, renderers, status
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics
from rest_framework.generics import UpdateAPIView

from django_rest_passwordreset.models import ResetPasswordToken
from django_rest_passwordreset.views import get_password_reset_token_expiry_time
from django_rest_passwordreset.signals import reset_password_token_created

from main.serializers import RegisterSerializer, LoginSerializer, UserSerializer
from main.serializers import ChangePasswordSerializer
from main.serializers import CustomTokenSerializer


class UserRegisterView(ListCreateAPIView):
    create_queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_user = serializer.save()
        token = AuthToken.objects.create(new_user)[1]
        return Response(
            {
                "user": UserSerializer(
                    new_user, context=self.get_serializer_context()
                ).data,
                "token": token,
            }
        )


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data
        login(request, user)
        token = AuthToken.objects.create(user)[1]

        return Response(
            {
                "user": UserSerializer(
                    user, context=self.get_serializer_context()
                ).data,
                "token": token,
            }
        )


class UserAPI(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.object = None

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            old_password = serializer.data.get("old_password")
            if not self.object.check_password(old_password):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response("Password updated successfully.")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomPasswordResetView:
    # pylint: disable=E0213, R0201
    @receiver(reset_password_token_created)
    def password_reset_token_created(sender, reset_password_token, *args, **kwargs):
        """
        Handles password reset tokens
        When a token is created, an e-mail needs to be sent to the user
        """
        # send an e-mail to the user
        context = {
            "current_user": reset_password_token.user,
            "username": reset_password_token.user.username,
            "email": reset_password_token.user.email,
            "password_reset_token": f"https://api.fennellabs.com/v1/auth/reset_password/{reset_password_token.key}",
        }

        # render email text
        email_html_message = render_to_string("email/user_reset_password.html", context)
        email_plaintext_message = render_to_string(
            "email/user_reset_password.txt", context
        )

        msg = EmailMultiAlternatives(
            # title:
            "Password Reset for Fennel Network",
            # message:
            email_plaintext_message,
            # from:
            "info@fennellabs.com",
            # to:
            [reset_password_token.user.email],
        )
        msg.attach_alternative(email_html_message, "text/html")
        msg.send()


class CustomPasswordTokenVerificationView(APIView):
    """
    An Api View which provides a method to verifiy that a given pw-reset token is valid before actually confirming the
    reset.
    """

    throttle_classes = ()
    permission_classes = ()
    parser_classes = (
        parsers.FormParser,
        parsers.MultiPartParser,
        parsers.JSONParser,
    )
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = CustomTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]

        # get token validation time
        password_reset_token_validation_time = get_password_reset_token_expiry_time()

        # find token
        reset_password_token = ResetPasswordToken.objects.filter(key=token).first()

        if reset_password_token is None:
            return Response({"status": "invalid"}, status=status.HTTP_404_NOT_FOUND)

        # check expiry date
        expiry_date = reset_password_token.created_at + timedelta(
            hours=password_reset_token_validation_time
        )

        if timezone.now() > expiry_date:
            # delete expired token
            reset_password_token.delete()
            return Response({"status": "expired"}, status=status.HTTP_404_NOT_FOUND)

        # check if user has password to change
        if not reset_password_token.user.has_usable_password():
            return Response({"status": "irrelevant"})

        return Response({"status": "OK"})
