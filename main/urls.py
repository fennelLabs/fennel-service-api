from django.urls import path
from knox import views as knox_views

from main import views, auth_views, whiteflag_views

urlpatterns = [
    path("healthcheck/", views.healthcheck),
    path("whiteflag/healthcheck/", whiteflag_views.fennel_cli_healthcheck),
    path("fennel/healthcheck/", views.subservice_healthcheck),
    path("whiteflag/authenticate/", whiteflag_views.whiteflag_authenticate),
    path(
        "whiteflag/discontinue_authentication/",
        whiteflag_views.whiteflag_discontinue_authentication,
    ),
    path("whiteflag/encode/", whiteflag_views.whiteflag_encode),
    path("whiteflag/decode/", whiteflag_views.whiteflag_decode),
    path(
        "whiteflag/generate_shared_token/",
        whiteflag_views.whiteflag_generate_shared_token,
    ),
    path(
        "whiteflag/generate_public_token/",
        whiteflag_views.whiteflag_generate_public_token,
    ),
    path("fennel/create_account/", views.create_account),
    path("fennel/get_account_balance/", views.get_account_balance),
    path("fennel/get_address/", views.get_address),
    path("fennel/get_fee_for_transfer_token/", views.get_fee_for_transfer_token),
    path("fennel/transfer_token/", views.transfer_token),
    path("fennel/get_fee_for_new_signal/", views.get_fee_for_new_signal),
    path("fennel/send_new_signal/", views.send_new_signal),
    path("fennel/get_fee_for_sync_signal/", views.get_fee_for_sync_signal),
    path("fennel/sync_signal/", views.sync_signal),
    path("fennel/get_signals/", views.get_signals),
    path("fennel/get_signals/<int:count>/", views.get_signals),
    path("fennel/get_signal_history/", views.get_signal_history),
    path("fennel/get_unsynced_signals/", views.get_unsynced_signals),
    path("fennel/get_fee_history/", views.get_fee_history),
    path("fennel/get_fee_history/<int:count>/", views.get_fee_history),
    path("auth/register/", auth_views.UserRegisterView.as_view()),
    path("auth/login/", auth_views.LoginAPIView.as_view()),
    path("auth/user/", auth_views.UserAPI.as_view()),
    path("auth/logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
]
