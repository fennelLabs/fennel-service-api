from django.test.client import Client
from django.contrib.auth import get_user_model

from main.models import UserKeys


def test_get_public_key_by_username():
    client = Client()
    User = get_user_model()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "public_key_by_username_test",
            "password": "test",
            "email": "public_key_by_username_test@test.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    user = User.objects.get(username="public_key_by_username_test")
    UserKeys.objects.update_or_create(
        user=user,
        public_diffie_hellman_key="test",
        private_diffie_hellman_key="test",
    )
    response = client.post(
        "/v1/crypto/get_public_key_by_username/",
        {"username": "public_key_by_username_test"},
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["public_key"] is not None
    assert response.json()["public_key"] == "test"
    User.objects.all().delete()
    UserKeys.objects.all().delete()


def test_get_public_key_by_address():
    client = Client()
    User = get_user_model()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "public_key_by_address_test",
            "password": "test",
            "email": "public_key_by_address_test@test.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    user = User.objects.get(username="public_key_by_address_test")
    UserKeys.objects.update_or_create(
        user=user,
        public_diffie_hellman_key="test",
        private_diffie_hellman_key="test",
        address="test",
    )
    response = client.post(
        "/v1/crypto/get_public_key_by_address/",
        {"address": "test"},
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["public_key"] is not None
    assert response.json()["public_key"] == "test"
    User.objects.all().delete()
    UserKeys.objects.all().delete()
