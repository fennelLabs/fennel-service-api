from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import APIGroup
import secrets


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_new_api_group(request):
    if APIGroup.objects.filter(user_list__in=[request.user]).exists():
        return Response({"message": "You already have an api group"}, status=400)
    if APIGroup.objects.filter(name=request.data["api_group_name"]).exists():
        return Response({"message": "Api Group already exists"}, status=400)
    api_group = APIGroup.objects.create(name=request.data["api_group_name"])
    if api_group.admin_list.filter(id=request.user.id).exists():
        return Response(
            {"message": "You are already admin of this api group"}, status=400
        )
    api_group.admin_list.add(request.user)
    api_group.user_list.add(request.user)
    api_group.api_key = secrets.token_hex(32)
    api_group.api_secret = secrets.token_hex(32)
    api_group.save()
    return Response(
        {
            "api_key": api_group.api_key,
            "api_secret": api_group.api_secret,
            "api_group_name": api_group.name,
        }
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def add_user_to_api_group(request):
    User = get_user_model()
    user = get_object_or_404(User, username=request.data["username"])
    if APIGroup.objects.filter(user_list__in=[user]).exists():
        return Response({"message": "User already has an api group"}, status=400)
    api_group = get_object_or_404(APIGroup, name=request.data["api_group_name"])
    if api_group.user_list.filter(id=user.id).exists():
        return Response({"message": "User already in this api group"}, status=400)
    api_group.user_list.add(user)
    api_group.save()
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def remove_user_from_api_group(request):
    User = get_user_model()
    user = get_object_or_404(User, username=request.data["username"])
    api_group = get_object_or_404(APIGroup, name=request.data["api_group_name"])
    if not api_group.admin_list.filter(id=request.user.id).exists():
        return Response({"message": "You are not admin of this api group"})
    if not api_group.user_list.filter(id=user.id).exists():
        return Response({"message": "User not in this api group"})
    api_group.user_list.remove(user)
    api_group.save()
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_accounts_billable_count(request):
    api_group = get_object_or_404(APIGroup, name=request.data["api_group_name"])
    if not api_group.admin_list.filter(id=request.user.id).exists():
        return Response({"message": "You are not admin of this api group"})
    return Response({"count": api_group.user_list.count()})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_api_group_requests_count(request):
    api_group = get_object_or_404(APIGroup, name=request.data["api_group_name"])
    if not api_group.admin_list.filter(id=request.user.id).exists():
        return Response({"message": "You are not admin of this api group"})
    return Response({"count": api_group.request_counter})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def add_admin_to_api_group(request):
    User = get_user_model()
    user = get_object_or_404(User, username=request.data["username"])
    api_group = get_object_or_404(APIGroup, name=request.data["api_group_name"])
    if not api_group.admin_list.filter(id=request.user.id).exists():
        return Response({"message": "You are not admin of this api group"})
    if not api_group.user_list.filter(id=user.id).exists():
        return Response({"message": "User not in this api group"})
    if api_group.admin_list.filter(id=user.id).exists():
        return Response({"message": "User already admin of this api group"})
    api_group.admin_list.add(user)
    api_group.save()
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def remove_admin_from_api_group(request):
    User = get_user_model()
    user = get_object_or_404(User, username=request.data["username"])
    api_group = get_object_or_404(APIGroup, name=request.data["api_group_name"])
    if not api_group.admin_list.filter(id=request.user.id).exists():
        return Response({"message": "You are not admin of this api group"})
    if not api_group.user_list.filter(id=user.id).exists():
        return Response({"message": "User not in this api group"})
    if not api_group.admin_list.filter(id=user.id).exists():
        return Response({"message": "User not admin of this api group"})
    api_group.admin_list.remove(user)
    api_group.save()
    return Response(status=status.HTTP_200_OK)
