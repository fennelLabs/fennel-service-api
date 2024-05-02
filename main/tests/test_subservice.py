from django.test import TestCase
from django.test.client import Client
from django.contrib.auth import get_user_model

from main.models import UserKeys


class TestFennelViews(TestCase):
    def test_create_account(self):
        client = Client()
        auth_response = client.post(
            "/api/v1/auth/register/",
            {"username": "test", "password": "test", "email": "test@test.com"},
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["token"] is not None
        user_model = get_user_model()
        user = user_model.objects.get(username="test")
        account_response = client.post(
            "/api/v1/fennel/create_account/",
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        user.delete()

        assert account_response.status_code == 200
        assert account_response.json()

    def test_create_account_userkey_exists_no_mnemonic(self):
        client = Client()
        auth_response = client.post(
            "/api/v1/auth/register/",
            {"username": "test", "password": "test", "email": "test@test.com"},
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["token"] is not None
        user_model = get_user_model()
        user = user_model.objects.get(username="test")
        UserKeys.objects.create(user=user)
        account_response = client.post(
            "/api/v1/fennel/create_account/",
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        user.delete()

        assert account_response.status_code == 200
        assert account_response.json()

    def test_create_account_mnemomic_exists(self):
        client = Client()
        auth_response = client.post(
            "/api/v1/auth/register/",
            {"username": "test", "password": "test", "email": "test@test.com"},
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["token"] is not None
        user_model = get_user_model()
        user = user_model.objects.get(username="test")
        client.post(
            "/api/v1/fennel/create_account/",
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        account_response = client.post(
            "/api/v1/fennel/create_account/",
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        user.delete()

        assert account_response.status_code == 400
        assert account_response.json()["error"] == "user already has an account"

    def test_get_account_balance_no_account(self):
        client = Client()
        response = client.post(
            "/api/v1/auth/register/",
            {"username": "test", "password": "test", "email": "test@test.com"},
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        user_model = get_user_model()
        response = client.post(
            "/api/v1/fennel/get_account_balance/",
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        user_model.objects.get(username="test").delete()
        assert response.status_code == 400
        assert response.json()["error"] == "user does not have a blockchain account"
