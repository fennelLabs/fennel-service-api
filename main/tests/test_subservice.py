from django.test.client import Client
from django.contrib.auth import get_user_model

from main.models import UserKeys


def test_create_account():
    client = Client()
    auth_response = client.post(
        "/v1/auth/register/",
        {"username": "test", "password": "test", "email": "test@test.com"},
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user_model = get_user_model()
    user = user_model.objects.get(username="test")
    account_response = client.post(
        "/v1/fennel/create_account/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    user.delete()
    UserKeys.objects.all().delete()
    assert account_response.status_code == 200
    assert account_response.json()


def test_create_account_userkey_exists_no_mnemonic():
    client = Client()
    auth_response = client.post(
        "/v1/auth/register/",
        {"username": "test", "password": "test", "email": "test@test.com"},
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user_model = get_user_model()
    user = user_model.objects.get(username="test")
    UserKeys.objects.create(user=user)
    account_response = client.post(
        "/v1/fennel/create_account/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    user.delete()
    UserKeys.objects.all().delete()
    assert account_response.status_code == 200
    assert account_response.json()


def test_create_account_mnemomic_exists():
    client = Client()
    auth_response = client.post(
        "/v1/auth/register/",
        {"username": "test", "password": "test", "email": "test@test.com"},
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user_model = get_user_model()
    user = user_model.objects.get(username="test")
    client.post(
        "/v1/fennel/create_account/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    account_response = client.post(
        "/v1/fennel/create_account/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    user.delete()
    UserKeys.objects.all().delete()
    assert account_response.status_code == 200
    assert account_response.json()["error"] == "user already has an account"


def test_get_account_balance_no_account():
    client = Client()
    response = client.post(
        "/v1/auth/register/",
        {"username": "test", "password": "test", "email": "test@test.com"},
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    user_model = get_user_model()
    response = client.post(
        "/v1/fennel/get_account_balance/",
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    user_model.objects.get(username="test").delete()
    assert response.status_code == 200
    assert response.json()["error"] == "user does not have an account"
