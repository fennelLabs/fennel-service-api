from django.test.client import Client
from django.contrib.auth import get_user_model

from main.models import UserKeys


def test_get_dh_public_key_by_username():
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
        "/v1/crypto/dh/get_public_key_by_username/",
        {"username": "public_key_by_username_test"},
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["public_key"] is not None
    assert response.json()["public_key"] == "test"
    User.objects.all().delete()
    UserKeys.objects.all().delete()


def test_get_dh_public_key_by_address():
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
        "/v1/crypto/dh/get_public_key_by_address/",
        {"address": "test"},
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["public_key"] is not None
    assert response.json()["public_key"] == "test"
    User.objects.all().delete()
    UserKeys.objects.all().delete()


def test_check_if_encrypted():
    client = Client()
    User = get_user_model()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "check_if_encrypted_test",
            "password": "test",
            "email": "check_if_encrypted_test@test.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    response = client.post(
        "/v1/crypto/dh/whiteflag/is_this_encrypted/",
        {
            "message": "5746313020a00000000000000000000000000000000000000000000000000000000000000000b43a3a38399d1797b7b933b0b734b9b0ba34b7b71734b73a17bbb434ba32b33630b380"
        },
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["encrypted"] is not None
    assert response.json()["encrypted"] == False
    User.objects.all().delete()


def test_check_if_encrypted_true():
    client = Client()
    User = get_user_model()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "check_if_encrypted_test",
            "password": "test",
            "email": "check_if_encrypted_test@test.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    response = client.post(
        "/v1/crypto/dh/whiteflag/is_this_encrypted/",
        {
            "message": "5746313124b391437103a277601f9eb073db2e99e36ab879935cdb6212c1adf42879daae0aad3894c6ef9f5bff7e32e1549e6e58f4a0e539547cc31b4d6ddeb170d3519cdf7f6cd5e6336232ce2a262748abf37ad9194487bbb29b4d16dfae8e1d65cad70494784f91ce1cf27142066b63f26431aa7643ae811c0c4c0d35eedaabe37a6412086c908489795177d3f9b363c8b48004c5951249a8878258c1147648e9f75644a236a50b08d0255f9ea605bd37ed283"
        },
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["encrypted"] is not None
    assert response.json()["encrypted"] == True
    User.objects.all().delete()
