import os
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
from django.core.mail import send_mail

from main.forms import APIGroupForm
from .models import APIGroup, UserKeys
import secrets
from silk.profiling.profiler import silk_profile


@silk_profile(name="create_new_api_group")
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_new_api_group(request):
    form = APIGroupForm(request.data)
    if not form.is_valid():
        return Response({"error": dict(form.errors.items())}, status=400)
    if APIGroup.objects.filter(user_list__in=[request.user]).exists():
        return Response({"message": "You already have an api group"}, status=400)
    if APIGroup.objects.filter(name=form.cleaned_data["api_group_name"]).exists():
        return Response({"message": "Api Group already exists"}, status=400)
    api_group = APIGroup.objects.create(
        name=form.cleaned_data["api_group_name"], email=form.cleaned_data["email"]
    )
    if api_group.admin_list.filter(id=request.user.id).exists():
        return Response(
            {"message": "You are already admin of this api group"}, status=400
        )
    api_group.admin_list.add(request.user)
    api_group.user_list.add(request.user)
    api_group.api_key = secrets.token_hex(32)
    api_group.api_secret = secrets.token_hex(32)
    api_group.save()
    send_mail(
        "New API Group",
        f"A new API Group has been added with the name {api_group.name} and the email {api_group.email}",
        os.environ.get("SERVER_EMAIL"),
        [os.environ.get("SERVER_EMAIL")],
    )
    return Response(
        {
            "api_key": api_group.api_key,
            "api_secret": api_group.api_secret,
            "api_group_name": api_group.name,
        }
    )


@silk_profile(name="get_api_group_keys")
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


@silk_profile(name="add_user_to_api_group")
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


@silk_profile(name="remove_user_from_api_group")
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_accounts_billable_count(request):
    api_group = get_object_or_404(APIGroup, name=request.data["api_group_name"])
    if not api_group.admin_list.filter(id=request.user.id).exists():
        return Response({"message": "You are not admin of this api group"})
    return Response({"count": api_group.user_list.count()})


@silk_profile(name="get_accounts_billable_count")
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_api_group_requests_count(request):
    api_group = get_object_or_404(APIGroup, name=request.data["api_group_name"])
    if not api_group.admin_list.filter(id=request.user.id).exists():
        return Response({"message": "You are not admin of this api group"})
    return Response({"count": api_group.request_counter})


@silk_profile(name="get_api_group_requests_count")
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


@silk_profile(name="add_admin_to_api_group")
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


@silk_profile(name="remove_admin_from_api_group")
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_api_group_users(request):
    api_group = get_object_or_404(APIGroup, name=request.data["api_group_name"])
    if not api_group.user_list.filter(id=request.user.id).exists():
        return Response({"message": "You are not a member of this api group"})
    user_keys = UserKeys.objects.filter(user__in=api_group.user_list.all())
    return Response(
        [
            {
                "username": user.user.username,
                "mnemonic": user.mnemonic,
                "public_key": user.public_diffie_hellman_key,
            }
            for user in user_keys
        ]
    )
