from django.shortcuts import redirect
from django.urls import reverse

from dashboard.models import UserKeys


def require_authentication(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        return redirect(reverse("dashboard:login"))

    return wrapper


def require_admin(view_func):
    def wrapper(request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and request.user.api_group_admins.all().exists()
        ):
            return view_func(request, *args, **kwargs)
        return redirect(reverse("dashboard:index"))

    return wrapper


def require_mnemonic_created(view_func):
    def wrapper(request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and UserKeys.objects.filter(user=request.user).exists()
            and UserKeys.objects.get(user=request.user).mnemonic is not None
        ):
            return view_func(request, *args, **kwargs)
        return redirect(reverse("dashboard:generate_mnemonic"))

    return wrapper
