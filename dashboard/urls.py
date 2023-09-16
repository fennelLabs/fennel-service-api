from django.urls import path
from django.contrib.auth import views as django_auth_views

from dashboard import auth_views, views, admin_views


# pylint: disable=invalid-name
app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    # Custom auth views
    path("register/", auth_views.registration_view, name="register"),
    path("login/", auth_views.login_view, name="login"),
    path("logout/", auth_views.logout_view, name="logout"),
    path("change-password/", auth_views.change_password_view, name="change_password"),
    # Admin dashboard views
    path(
        "create_wallet/<int:group_id>/", admin_views.create_wallet, name="create_wallet"
    ),
    path(
        "members/<int:group_id>/create_wallet/<int:member_id>/",
        admin_views.create_wallet_for_member,
        name="create_wallet_for_member",
    ),
    path(
        "join-requests/<int:group_id>/",
        admin_views.api_group_join_requests,
        name="api_group_join_requests",
    ),
    path(
        "join-requests/<int:group_id>/accept/<int:request_id>/",
        admin_views.accept_join_request,
        name="accept_join_request",
    ),
    path(
        "join-requests/<int:group_id>/reject/<int:request_id>/",
        admin_views.reject_join_request,
        name="reject_join_request",
    ),
    path(
        "members/<int:group_id>/",
        admin_views.api_group_members,
        name="api_group_members",
    ),
    path(
        "members/<int:group_id>/remove/<int:member_id>/",
        admin_views.remove_group_member,
        name="remove_group_member",
    ),
    path(
        "members/<int:group_id>/transfer/<int:member_id>/",
        admin_views.transfer_tokens_to_member,
        name="transfer_tokens_to_member",
    ),
    path(
        "members/<int:group_id>/transfer/<int:member_id>/confirm/",
        admin_views.confirm_transfer_tokens_to_member,
        name="confirm_transfer_tokens_to_member",
    ),
    # Django's built-in password reset views
    path(
        "password-reset/",
        django_auth_views.PasswordResetView.as_view(
            template_name="auth/password_reset.html"
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        django_auth_views.PasswordResetDoneView.as_view(
            template_name="auth/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        django_auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        django_auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
