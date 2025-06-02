from django.contrib import messages
from django.contrib.auth import logout, login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from silk.profiling.profiler import silk_profile

from dashboard.decorators import require_authentication
from dashboard.forms import LoginForm, RegistrationForm


def redirect_authenticated_user(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse("dashboard:index"))
        return view_func(request, *args, **kwargs)

    return wrapper


@silk_profile(name="registration_view")
@redirect_authenticated_user
def registration_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("dashboard:login"))
    else:
        form = RegistrationForm()
    return render(request, "auth/register.html", {"form": form})


@silk_profile(name="login_view")
@redirect_authenticated_user
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request=request,
                username=form.cleaned_data.get("username"),
                password=form.cleaned_data.get("password"),
            )
            login(request, user)
            return redirect(reverse("dashboard:index"))
    else:
        form = LoginForm()
    return render(request, "auth/login.html", {"form": form})


@silk_profile(name="logout_view")
def logout_view(request):
    messages.get_messages(request).used = True
    logout(request)
    return redirect(reverse("dashboard:login"))


@silk_profile(name="change_password_view")
@require_authentication
def change_password_view(request):
    messages.get_messages(request).used = True
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            user.save()
            messages.success(request, _("Your password was successfully updated!"))
            return redirect(reverse("dashboard:index"))
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "auth/change_password.html", {"form": form})
