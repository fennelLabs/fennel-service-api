from django.test.client import Client
from django.contrib.auth import get_user_model

from main.models import UserKeys


def test_create_account_user_exists():
    client = Client()
    response = client.post(
        "/v1/auth/register/",
        {"username": "test", "password": "test", "email": "test@test.com"},
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    User = get_user_model()
    user = User.objects.get(username="test")
    keys = UserKeys.objects.create(user=user)
    account_response = client.post(
        "/v1/fennel/create_account/",
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    user.delete()
    keys.delete()
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
    User = get_user_model()
    response = client.post(
        "/v1/fennel/get_account_balance/",
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    User.objects.get(username="test").delete()
    assert response.status_code == 200
    assert response.json()["error"] == "user does not have an account"
