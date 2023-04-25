from main.models import User
from main.serializers import (
    UserSerializer,
)
from rest_framework import viewsets, views
from rest_framework.response import Response
import django_filters.rest_framework


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['name', 'email', 'password']


class WhiteflagSignalView(views.APIView):
    def get(self, request, format=None):
        return Response({'signal': 'ok'})

    def post(self, request, format=None):
        return Response({'signal': 'ok'})
