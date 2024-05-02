from django.test import Client
from django.test import TestCase

from model_bakery import baker

from main.models import APIGroup


class TestAPIGroupViews(TestCase):
    def test_get_group_list(self):
        client = Client()
        auth_response = client.post(
            "/api/v1/auth/register/",
            {
                "username": "test_generate_apigroup_keypair",
                "password": "testpassword",
                "email": "test_generate_apigroup_keypair@test.com",
            },
        )
        token = auth_response.json()["token"]
        baker.make("main.APIGroup", _quantity=10)
        response = client.get(
            "/api/v1/group/get_list/", HTTP_AUTHORIZATION=f"Token {token}"
        )
        assert response.status_code == 200
        assert len(response.json()) == 10

    def test_generate_apigroup_keypair(self):
        client = Client()
        auth_response = client.post(
            "/api/v1/auth/register/",
            {
                "username": "test_generate_apigroup_keypair",
                "password": "testpassword",
                "email": "test_generate_apigroup_keypair@test.com",
            },
        )
        auth_response_two = client.post(
            "/api/v1/auth/register/",
            {
                "username": "test_generate_apigroup_keypair_two",
                "password": "testpassword",
                "email": "test_generate_apigroup_keypair_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/api/v1/auth/login/",
            {"username": "test_generate_apigroup_keypair", "password": "testpassword"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        assert token is not None
        response = client.post(
            "/api/v1/group/create/",
            {
                "api_group_name": "test_generate_apigroup_keypair",
                "email": "test_generate_apigroup_keypair@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_generate_apigroup_keypair")
        assert group is not None
        assert group.name == "test_generate_apigroup_keypair"
        assert group.admin_list.filter(
            username="test_generate_apigroup_keypair"
        ).exists()
        response = client.post(
            "/api/v1/group/generate_keypair/",
            {
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert response.json()["secret"] is not None
        assert response.json()["public"] is not None

    def test_get_apigroup_keypair(self):
        client = Client()
        auth_response = client.post(
            "/api/v1/auth/register/",
            {
                "username": "test_get_apigroup_keypair",
                "password": "testpassword",
                "email": "test_get_apigroup_keypair@test.com",
            },
        )
        auth_response_two = client.post(
            "/api/v1/auth/register/",
            {
                "username": "test_get_apigroup_keypair_two",
                "password": "testpassword",
                "email": "test_get_apigroup_keypair_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/api/v1/auth/login/",
            {"username": "test_get_apigroup_keypair", "password": "testpassword"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        assert token is not None
        response = client.post(
            "/api/v1/group/create/",
            {
                "api_group_name": "test_get_apigroup_keypair",
                "email": "test_get_apigroup_keypair@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_get_apigroup_keypair")
        assert group is not None
        assert group.name == "test_get_apigroup_keypair"
        assert group.admin_list.filter(username="test_get_apigroup_keypair").exists()
        response = client.post(
            "/api/v1/group/generate_keypair/",
            {
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        response = client.post(
            "/api/v1/group/get_keypair/",
            {
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert response.json()["public"] is not None
        assert response.json()["secret"] is not None

    def test_get_apigroup_keypair_none_created(self):
        client = Client()
        auth_response = client.post(
            "/api/v1/auth/register/",
            {
                "username": "test_get_apigroup_keypair",
                "password": "testpassword",
                "email": "test_get_apigroup_keypair@test.com",
            },
        )
        auth_response_two = client.post(
            "/api/v1/auth/register/",
            {
                "username": "test_get_apigroup_keypair_two",
                "password": "testpassword",
                "email": "test_get_apigroup_keypair_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/api/v1/auth/login/",
            {"username": "test_get_apigroup_keypair", "password": "testpassword"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        assert token is not None
        response = client.post(
            "/api/v1/group/create/",
            {
                "api_group_name": "test_get_apigroup_keypair",
                "email": "test_get_apigroup_keypair@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_get_apigroup_keypair")
        assert group is not None
        assert group.name == "test_get_apigroup_keypair"
        assert group.admin_list.filter(username="test_get_apigroup_keypair").exists()
        response = client.post(
            "/api/v1/group/get_keypair/",
            {
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 400
        assert response.json()["error"] is not None
