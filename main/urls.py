from django.urls import path
from knox import views as knox_views

from main import views, auth_views, whiteflag_views, crypto_views, fennel_views

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
    path(
        "crypto/dh/whiteflag/is_this_encrypted/",
        crypto_views.wf_is_this_encrypted,
    ),
    path(
        "crypto/dh/generate_keypair/",
        crypto_views.generate_diffie_hellman_keypair,
    ),
    path(
        "crypto/dh/get_shared_secret/",
        crypto_views.get_diffie_hellman_shared_secret,
    ),
    path(
        "crypto/dh/whiteflag/encrypt_message/",
        crypto_views.dh_encrypt_whiteflag_message,
    ),
    path(
        "crypto/dh/whiteflag/decrypt_message/",
        crypto_views.dh_decrypt_whiteflag_message,
    ),
    path(
        "crypto/dh/get_public_key_by_username/",
        crypto_views.get_dh_public_key_by_username,
    ),
    path(
        "crypto/dh/get_public_key_by_address/",
        crypto_views.get_dh_public_key_by_address,
    ),
    path("fennel/create_account/", fennel_views.create_account),
    path("fennel/get_account_balance/", fennel_views.get_account_balance),
    path("fennel/get_address/", fennel_views.get_address),
    path("fennel/get_fee_for_transfer_token/", fennel_views.get_fee_for_transfer_token),
    path("fennel/transfer_token/", fennel_views.transfer_token),
    path("fennel/get_fee_for_new_signal/", fennel_views.get_fee_for_new_signal),
    path("fennel/send_new_signal/", fennel_views.send_new_signal),
    path("fennel/get_fee_for_sync_signal/", fennel_views.get_fee_for_sync_signal),
    path("fennel/sync_signal/", fennel_views.sync_signal),
    path("fennel/confirm_signal/", fennel_views.confirm_signal),
    path("fennel/get_signals/", fennel_views.get_signals),
    path("fennel/get_signals/<int:count>/", fennel_views.get_signals),
    path("fennel/get_unsynced_signals/", fennel_views.get_unsynced_signals),
    path("fennel/get_fee_history/", fennel_views.get_fee_history),
    path("fennel/get_fee_history/<int:count>/", fennel_views.get_fee_history),
    path("auth/register/", auth_views.UserRegisterView.as_view()),
    path("auth/login/", auth_views.LoginAPIView.as_view()),
    path("auth/user/", auth_views.UserAPI.as_view()),
    path("auth/logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
]
