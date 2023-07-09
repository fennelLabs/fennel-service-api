from django.test.client import Client
from django.contrib.auth import get_user_model
from main.models import Transaction, Signal
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
