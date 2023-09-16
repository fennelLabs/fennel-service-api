from django.shortcuts import redirect
from django.urls import reverse


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
