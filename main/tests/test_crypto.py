from django.test import TestCase
from django.test.client import Client
from django.contrib.auth import get_user_model

from main.models import UserKeys


class TestCryptoViews(TestCase):
    def test_get_dh_public_key_by_username(self):
        client = Client()
        user_model = get_user_model()
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
        user = user_model.objects.get(username="public_key_by_username_test")
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
        user_model.objects.all().delete()
        UserKeys.objects.all().delete()

    def test_get_dh_public_key_by_address(self):
        client = Client()
        user_model = get_user_model()
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
        user = user_model.objects.get(username="public_key_by_address_test")
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
        user_model.objects.all().delete()
        UserKeys.objects.all().delete()

    def test_check_if_encrypted(self):
        client = Client()
        user_model = get_user_model()
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
        assert not response.json()["encrypted"]
        user_model.objects.all().delete()

    def test_check_if_encrypted_true(self):
        client = Client()
        user_model = get_user_model()
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
        assert response.json()["encrypted"]
        user_model.objects.all().delete()

    def test_encrypt_message(self):
        client = Client()
        user_model = get_user_model()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "encrypt_message_test",
                "password": "test",
                "email": "encrypt_message_test@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        response = client.post(
            "/v1/crypto/dh/whiteflag/encrypt_message/",
            {
                "message": "574631312af34c38e3af3ab687ac276965c11b369274da9ddf514bcc0eebf037a268f087f3bda708026b5f7a5b83e49072a2d32f83bc283c249601066c488a0a1e40bb4f27dcb409c14aa7c7b7f0f656c9bc184a8df6fbe7928a25d3e5b74a81ab16df93efcc30b1105c7ba56878afed34f318d337532a293b41c7b54d1af2c6b92414a79e68077655f7e3629bf93b2f43e553ebd518198c2cc1a782bcc3d37e1304f431c9997c803368f54ef2f2774f42543c32d",
                "shared_secret": "bc9fc6e2629eddd82ec1bdfae268288de8db724e12ebd3eb6f99d9a686cc457e",
            },
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
        assert response.json()["encrypted"] is not None
        user_model.objects.all().delete()

    def test_decrypt_message(self):
        client = Client()
        user_model = get_user_model()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "decrypt_message_test",
                "password": "test",
                "email": "decrypt_message_test@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        response = client.post(
            "/v1/crypto/dh/whiteflag/decrypt_message/",
            {
                "message": "574631312af34c38e3af3ab687ac276965c11b369274da9ddf514bcc0eebf037a268f087f3bda708026b5f7a5b83e49072a2d32f83bc283c249601066c488a0a1e40bb4f27dcb409c14aa7c7b7f0f656c9bc184a8df6fbe7928a25d3e5b74a81ab16df93efcc30b1105c7ba56878afed34f318d337532a293b41c7b54d1af2c6b92414a79e68077655f7e3629bf93b2f43e553ebd518198c2cc1a782bcc3d37e1304f431c9997c803368f54ef2f2774f42543c32d",
                "shared_secret": "bc9fc6e2629eddd82ec1bdfae268288de8db724e12ebd3eb6f99d9a686cc457e",
            },
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
        assert response.json()["decrypted"] is not None
        user_model.objects.all().delete()

    def test_get_my_keypair(self):
        client = Client()
        user_model = get_user_model()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "get_my_keypair_test",
                "password": "test",
                "email": "get_my_keypair_test@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        user = user_model.objects.get(username="get_my_keypair_test")
        UserKeys.objects.update_or_create(
            user=user,
            public_diffie_hellman_key="test",
            private_diffie_hellman_key="test",
        )
        response = client.post(
            "/v1/crypto/dh/get_my_keypair/",
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
        assert response.json()["public_key"] is not None
        assert response.json()["public_key"] == "test"
        assert response.json()["private_key"] is not None
        assert response.json()["private_key"] == "test"
        user_model.objects.all().delete()
        UserKeys.objects.all().delete()

    def test_get_my_keypair_no_keys(self):
        client = Client()
        user_model = get_user_model()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "get_my_keypair_no_keys_test",
                "password": "test",
                "email": "get_my_keypair_no_keys_test@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        user = user_model.objects.get(username="get_my_keypair_no_keys_test")
        UserKeys.objects.update_or_create(
            user=user,
        )
        response = client.post(
            "/v1/crypto/dh/get_my_keypair/",
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
        assert response.json()["public_key"] is None
        assert response.json()["private_key"] is None
        user_model.objects.all().delete()
        UserKeys.objects.all().delete()
