from django.test.client import Client
from django.contrib.auth import get_user_model
from model_bakery import baker
from main.models import Transaction, Signal, ConfirmationRecord, UserKeys
from main.fennel_views import (
    __record_signal_fee,
)


def test_create_account():
    client = Client()
    user_model = get_user_model()
    auth_response = client.post(
        "/v1/auth/register/",
        {
            "username": "create_account_test",
            "password": "test",
            "email": "create_account_test@test.com",
        },
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    response = client.post(
        "/v1/fennel/create_account/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    response = client.post(
        "/v1/fennel/get_address/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["address"] is not None
    user_model.objects.all().delete()


def test_get_fee_history_count():
    for _ in range(100):
        baker.make("main.Transaction")
    client = Client()
    user_model = get_user_model()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "fee_history_count_test",
            "password": "test",
            "email": "fee_history_count_test@test.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    response = client.get(
        "/v1/fennel/get_fee_history/10/",
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert len(response.json()) == 10
    Transaction.objects.all().delete()
    user_model.objects.all().delete()


def test_get_fee_history():
    for _ in range(100):
        baker.make("main.Transaction")
    client = Client()
    user_model = get_user_model()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "fee_history_test",
            "password": "fee_historytest",
            "email": "fee_history_test@test.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    response = client.get(
        "/v1/fennel/get_fee_history/",
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert len(response.json()) == 100
    Transaction.objects.all().delete()
    user_model.objects.all().delete()


def test_get_signals():
    client = Client()
    user_model = get_user_model()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "signals_test",
            "password": "signals_test",
            "email": "signals_test@test.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    user = user_model.objects.get(username="signals_test")
    UserKeys.objects.update_or_create(
        user=user,
        address="test",
    )
    for _ in range(100):
        baker.make("main.Signal", sender=user)
    response = client.get(
        "/v1/fennel/get_signals/",
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert len(response.json()) == 100
    Signal.objects.all().delete()
    user_model.objects.all().delete()


def test_confirm_signal():
    client = Client()
    user_model = get_user_model()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "confirm_signal_test",
            "password": "confirm_signal_test",
            "email": "confirm_signal_test@test.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    user = user_model.objects.get(username="confirm_signal_test")
    signal = baker.make("main.Signal", sender=user)
    response = client.post(
        "/v1/fennel/confirm_signal/",
        {"id": signal.id},
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    confirmation = ConfirmationRecord.objects.get(signal=signal)
    assert confirmation is not None
    assert confirmation.confirmer == user
    Signal.objects.all().delete()
    user_model.objects.all().delete()
    ConfirmationRecord.objects.all().delete()


def test_confirm_signal_updates():
    client = Client()
    user_model = get_user_model()
    auth_response = client.post(
        "/v1/auth/register/",
        {
            "username": "confirm_signal_test",
            "password": "confirm_signal_test",
            "email": "confirm_signal_test@test.com",
        },
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user = user_model.objects.get(username="confirm_signal_test")
    signal = baker.make("main.Signal", sender=user)
    response = client.post(
        "/v1/fennel/confirm_signal/",
        {"id": signal.id},
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    confirmation = ConfirmationRecord.objects.get(signal=signal)
    assert confirmation is not None
    assert confirmation.confirmer == user
    response = client.post(
        "/v1/fennel/confirm_signal/",
        {"id": signal.id},
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert len(ConfirmationRecord.objects.filter(signal=signal)) == 1
    Signal.objects.all().delete()
    user_model.objects.all().delete()
    ConfirmationRecord.objects.all().delete()


def test_signal_confirmation_list():
    client = Client()
    user_model = get_user_model()
    auth_response = client.post(
        "/v1/auth/register/",
        {
            "username": "confirm_signal_list_test",
            "password": "confirm_signal_list_test",
            "email": "confirm_signal_list_test@test.com",
        },
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user = user_model.objects.get(username="confirm_signal_list_test")
    UserKeys.objects.update_or_create(
        user=user,
        address="test",
    )
    signal = baker.make("main.Signal", sender=user)
    response = client.post(
        "/v1/fennel/confirm_signal/",
        {"id": signal.id},
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    confirmation = ConfirmationRecord.objects.get(signal=signal)
    assert confirmation is not None
    assert confirmation.confirmer == user
    response = client.get(
        "/v1/fennel/get_signals/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert len(response.json()[0]["confirmations"]) == 1
    Signal.objects.all().delete()
    user_model.objects.all().delete()
    ConfirmationRecord.objects.all().delete()


def test_get_signals_address_included():
    client = Client()
    user_model = get_user_model()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "signals_test",
            "password": "signals_test",
            "email": "signals_test@test.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    user = user_model.objects.get(username="signals_test")
    UserKeys.objects.update_or_create(
        user=user,
        address="test",
    )
    for _ in range(100):
        baker.make("main.Signal", sender=user)
    response = client.get(
        "/v1/fennel/get_signals/",
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert len(response.json()) == 100
    assert response.json()[0]["sender"]["address"] == "test"
    Signal.objects.all().delete()
    user_model.objects.all().delete()


def test_get_signals_count():
    client = Client()
    user_model = get_user_model()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "signals_count_test",
            "password": "signals_count_test",
            "email": "signals_count_test@test.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    user = user_model.objects.get(username="signals_count_test")
    UserKeys.objects.update_or_create(
        user=user,
        address="test",
    )
    for _ in range(100):
        baker.make("main.Signal", sender=user)
    response = client.get(
        "/v1/fennel/get_signals/10/",
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert len(response.json()) == 10
    Signal.objects.all().delete()
    user_model.objects.all().delete()


def test_get_unsynced_signals():
    client = Client()
    user_model = get_user_model()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "unsynced_signals_test",
            "password": "unsynced_signals_test",
            "email": "unsynced_signals_test@test.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    user = user_model.objects.get(username="unsynced_signals_test")
    for _ in range(100):
        baker.make("main.Signal", sender=user)
    response = client.get(
        "/v1/fennel/get_unsynced_signals/",
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert len(response.json()) == 100
    Signal.objects.all().delete()
    user_model.objects.all().delete()


def test_record_signal_fee():
    client = Client()
    user_model = get_user_model()
    auth_response = client.post(
        "/v1/auth/register/",
        {
            "username": "record_signal_fee_test",
            "password": "record_signal_fee_test",
            "email": "record_signal_fee_test@test.com",
        },
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user = user_model.objects.get(username="record_signal_fee_test")
    response = client.post(
        "/v1/fennel/create_account/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    mnemonic_from_database = UserKeys.objects.filter(user=user).first().mnemonic
    payload = {
        "mnemonic": mnemonic_from_database,
        "content": "This is a test.",
    }
    response, success = __record_signal_fee(payload)
    assert success
    assert response["fee"] is not None
    assert response["fee"] > 0
    user_model.objects.all().delete()
    UserKeys.objects.all().delete()


def test_get_fee_for_new_signal():
    client = Client()
    user_model = get_user_model()
    auth_response = client.post(
        "/v1/auth/register/",
        {
            "username": "get_fee_for_new_signal_test",
            "password": "get_fee_for_new_signal_test",
            "email": "get_fee_for_new_signal_test@test.com",
        },
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user = user_model.objects.get(username="get_fee_for_new_signal_test")
    response = client.post(
        "/v1/fennel/create_account/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert UserKeys.objects.filter(user=user).first().mnemonic is not None
    assert UserKeys.objects.filter(user=user).first().mnemonic != ""
    payload = {
        "signal": "This is a test.",
    }
    response = client.post(
        "/v1/fennel/get_fee_for_new_signal/",
        payload,
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["fee"] is not None
    assert response.json()["fee"] > 0
    user_model.objects.all().delete()
    UserKeys.objects.all().delete()


def test_get_fee_for_new_signal_with_empty_signal():
    client = Client()
    user_model = get_user_model()
    auth_response = client.post(
        "/v1/auth/register/",
        {
            "username": "get_fee_for_new_signal_test_empty",
            "password": "get_fee_for_new_signal_test_empty",
            "email": "get_fee_for_new_signal_test_empty@test.com",
        },
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user = user_model.objects.get(username="get_fee_for_new_signal_test_empty")
    response = client.post(
        "/v1/fennel/create_account/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert UserKeys.objects.filter(user=user).first().mnemonic is not None
    assert UserKeys.objects.filter(user=user).first().mnemonic != ""
    payload = {
        "signal": "",
    }
    response = client.post(
        "/v1/fennel/get_fee_for_new_signal/",
        payload,
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    print(response.json())
    assert response.status_code == 400
    user_model.objects.all().delete()
    UserKeys.objects.all().delete()


def test_get_fee_for_new_signal_with_whiteflag_signal():
    client = Client()
    user_model = get_user_model()
    auth_response = client.post(
        "/v1/auth/register/",
        {
            "username": "get_fee_for_new_signal_test_whiteflag",
            "password": "get_fee_for_new_signal_test_whiteflag",
            "email": "get_fee_for_new_signal_test_whiteflag@test.com",
        },
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user = user_model.objects.get(username="get_fee_for_new_signal_test_whiteflag")
    response = client.post(
        "/v1/fennel/create_account/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert UserKeys.objects.filter(user=user).first().mnemonic is not None
    assert UserKeys.objects.filter(user=user).first().mnemonic != ""
    payload = {
        "signal": "5746313024a00000000000000000000000000000000000000000000000000000000000000002910118480881290000000114e4245102400706000000000000",
    }
    response = client.post(
        "/v1/fennel/get_fee_for_new_signal/",
        payload,
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["fee"] is not None
    assert response.json()["fee"] > 0
    user_model.objects.all().delete()
    UserKeys.objects.all().delete()


def test_get_address_no_error_when_userkeys_is_none():
    client = Client()
    user_model = get_user_model()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "no_error_when_address_is_none_test",
            "password": "no_error_when_address_is_none_test",
            "email": "no_error_when_address_is_none_test@test.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    response = client.post(
        "/v1/fennel/get_address/",
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 400
    user_model.objects.all().delete()
    UserKeys.objects.all().delete()
