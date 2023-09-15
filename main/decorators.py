from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from main.models import APIGroup, UserKeys


def fennel_admin_only(view_func):
    def wrap(request, *args, **kwargs):
        # Check if request.user is a FennelAdmin
        if request.user.groups.filter(name="FennelAdmin").exists():
            return view_func(request, *args, **kwargs)
        return Response({"error": "permission denied."}, status=400)

    return wrap


def requires_mnemonic_created(view_func):
    def wrap(request, *args, **kwargs):
        user_keys = UserKeys.objects.filter(user=request.user)
        if user_keys.exists() and user_keys.first().mnemonic:
            return view_func(request, *args, **kwargs)
        return Response(
            {
                "error": "user does not have a blockchain account",
                "fix": "call /v1/fennel/create_account first",
            },
            status=400,
        )

    return wrap


def subject_to_api_limit(view_func):
    def wrap(request, *args, **kwargs):
        api_key = request.data.get("api_key", None)
        api_secret = request.data.get("api_secret", None)
        if api_key and api_secret:
            api_group = get_object_or_404(
                APIGroup, api_key=api_key, api_secret=api_secret
            )
            if request.user not in api_group.user_list.all():
                return Response(
                    {"error": "you don't have access to this api group"}, status=400
                )
            if not api_group.active:
                return Response(
                    {
                        "error": "API access restricted. Please contact info@fennellabs.com."
                    },
                    status=400,
                )
            api_group.request_counter += 1
            api_group.save()
            return view_func(request, *args, **kwargs)
        return Response({"error": "API key and secret required."}, status=400)

    return wrap


def apigroup_admin_only(view_func):
    def wrap(request, *args, **kwargs):
        api_key = request.data.get("api_key", None)
        api_secret = request.data.get("api_secret", None)
        if api_key and api_secret:
            api_group = get_object_or_404(
                APIGroup, api_key=api_key, api_secret=api_secret
            )
            if request.user not in api_group.user_list.all():
                return Response(
                    {"error": "you don't have access to this api group"}, status=400
                )
            if request.user not in api_group.admin_list.all():
                return Response(
                    {"error": "you don't have admin access to this api group"},
                    status=400,
                )
        return view_func(request, *args, **kwargs)

    return wrap
