from django.test.client import Client
from django.contrib.auth import get_user_model
from main.models import Transaction, Signal, ConfirmationRecord, UserKeys
from model_bakery import baker


def test_get_fee_history_count():
    for _ in range(100):
        baker.make("main.Transaction")
    client = Client()
    User = get_user_model()
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
    User.objects.all().delete()


def test_get_fee_history():
    for _ in range(100):
        baker.make("main.Transaction")
    client = Client()
    User = get_user_model()
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
    User.objects.all().delete()


def test_get_signals():
    client = Client()
    User = get_user_model()
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
    user = User.objects.get(username="signals_test")
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
    User.objects.all().delete()


def test_confirm_signal():
    client = Client()
    User = get_user_model()
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
    user = User.objects.get(username="confirm_signal_test")
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
    User.objects.all().delete()
    ConfirmationRecord.objects.all().delete()


def test_confirm_signal_updates():
    client = Client()
    User = get_user_model()
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
    user = User.objects.get(username="confirm_signal_test")
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
    User.objects.all().delete()
    ConfirmationRecord.objects.all().delete()


def test_signal_confirmation_list():
    client = Client()
    User = get_user_model()
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
    user = User.objects.get(username="confirm_signal_list_test")
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
    print(response.json())
    assert len(response.json()[0]["confirmations"]) == 1
    Signal.objects.all().delete()
    User.objects.all().delete()
    ConfirmationRecord.objects.all().delete()


def test_get_signals_address_included():
    client = Client()
    User = get_user_model()
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
    user = User.objects.get(username="signals_test")
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
    User.objects.all().delete()


def test_get_signals_count():
    client = Client()
    User = get_user_model()
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
    user = User.objects.get(username="signals_count_test")
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
    User.objects.all().delete()


def test_get_unsynced_signals():
    client = Client()
    User = get_user_model()
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
    user = User.objects.get(username="unsynced_signals_test")
    for _ in range(100):
        baker.make("main.Signal", sender=user)
    response = client.get(
        "/v1/fennel/get_unsynced_signals/",
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert len(response.json()) == 100
    Signal.objects.all().delete()
    User.objects.all().delete()
