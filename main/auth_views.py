from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from rest_framework import generics
from knox.models import AuthToken
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from django.contrib.auth import login
from .serializers import ChangePasswordSerializer
from rest_framework.generics import UpdateAPIView
from rest_framework import status


class UserRegisterView(ListCreateAPIView):
    create_queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        newUser = serializer.save()
        token = AuthToken.objects.create(newUser)[1]
        return Response(
            {
                "user": UserSerializer(
                    newUser, context=self.get_serializer_context()
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
