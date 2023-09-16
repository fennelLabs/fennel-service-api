from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from main.models import APIGroup, UserKeys


class TestAPIAdminViews(TestCase):
    def test_create_new_api_group(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_create_new_api_group",
                "password": "testpassword",
                "email": "test_create_new_api_group@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["token"] is not None
        login_response = client.post(
            "/v1/auth/login/",
            {"username": "test_create_new_api_group", "password": "testpassword"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_create_new_api_group",
                "email": "test_create_new_api_group@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_create_new_api_group")
        assert group is not None
        assert group.admin_list.filter(username="test_create_new_api_group").exists()

    def test_add_user_to_api_group(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_add_user_to_api_group",
                "password": "testpassword",
                "email": "test_add_user_to_api_group@test.com",
            },
        )
        auth_response_two = client.post(
            "/v1/auth/register/",
            {
                "username": "test_add_user_to_api_group_two",
                "password": "testpassword",
                "email": "test_add_user_to_api_group_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/v1/auth/login/",
            {"username": "test_add_user_to_api_group", "password": "testpassword"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_add_user_to_api_group",
                "email": "test_add_user_to_api_group@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_add_user_to_api_group")
        assert group is not None
        assert group.admin_list.filter(username="test_add_user_to_api_group").exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_add_user_to_api_group",
                "username": "test_add_user_to_api_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_add_user_to_api_group_two"
        ).exists()

    def test_add_user_to_api_group_as_non_admin(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_add_user_to_api_group_as_non_admin",
                "password": "testpassword",
                "email": "test_add_user_to_api_group_as_non_admin@test.com",
            },
        )
        auth_response_two = client.post(
            "/v1/auth/register/",
            {
                "username": "test_add_user_to_api_group_as_non_admin_two",
                "password": "testpassword",
                "email": "test_add_user_to_api_group_as_non_admin_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/v1/auth/login/",
            {
                "username": "test_add_user_to_api_group_as_non_admin",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        login_response_two = client.post(
            "/v1/auth/login/",
            {
                "username": "test_add_user_to_api_group_as_non_admin_two",
                "password": "testpassword",
            },
        )
        assert login_response_two.status_code == 200
        token_two = login_response_two.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_add_user_to_api_group_as_non_admin",
                "email": "test_add_user_to_api_group_as_non_admin@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_add_user_to_api_group_as_non_admin")
        assert group is not None
        assert group.admin_list.filter(
            username="test_add_user_to_api_group_as_non_admin"
        ).exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_add_user_to_api_group_as_non_admin",
                "username": "test_add_user_to_api_group_as_non_admin_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token_two}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_add_user_to_api_group_as_non_admin_two"
        ).exists()

    def test_remove_user_from_api_group(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_user_from_api_group",
                "password": "testpassword",
                "email": "test_remove_user_from_api_group@test.com",
            },
        )
        auth_response_two = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_user_from_api_group_two",
                "password": "testpassword",
                "email": "test_remove_user_from_api_group_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/v1/auth/login/",
            {"username": "test_remove_user_from_api_group", "password": "testpassword"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_remove_user_from_api_group",
                "email": "test_remove_user_from_api_group@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_remove_user_from_api_group")
        assert group is not None
        assert group.admin_list.filter(
            username="test_remove_user_from_api_group"
        ).exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_remove_user_from_api_group",
                "username": "test_remove_user_from_api_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_remove_user_from_api_group_two"
        ).exists()
        response = client.post(
            "/v1/group/remove_user/",
            {
                "api_group_name": "test_remove_user_from_api_group",
                "username": "test_remove_user_from_api_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert not group.user_list.filter(
            username="test_remove_user_from_api_group_two"
        ).exists()

    def test_remove_user_from_api_group_as_non_admin(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_user_from_api_group",
                "password": "testpassword",
                "email": "test_remove_user_from_api_group@test.com",
            },
        )
        auth_response_two = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_user_from_api_group_two",
                "password": "testpassword",
                "email": "test_remove_user_from_api_group_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/v1/auth/login/",
            {"username": "test_remove_user_from_api_group", "password": "testpassword"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        token_two = auth_response_two.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_remove_user_from_api_group",
                "email": "test_remove_user_from_api_group@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_remove_user_from_api_group")
        assert group is not None
        assert group.admin_list.filter(
            username="test_remove_user_from_api_group"
        ).exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_remove_user_from_api_group",
                "username": "test_remove_user_from_api_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_remove_user_from_api_group_two"
        ).exists()
        response = client.post(
            "/v1/group/remove_user/",
            {
                "api_group_name": "test_remove_user_from_api_group",
                "username": "test_remove_user_from_api_group_two",
            },
            HTTP_AUTHORIZATION=f"Token {token_two}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_remove_user_from_api_group_two"
        ).exists()

    def test_remove_user_from_api_group_not_in_group(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_user_from_api_group",
                "password": "testpassword",
                "email": "test_remove_user_from_api_group@test.com",
            },
        )
        auth_response_two = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_user_from_api_group_two",
                "password": "testpassword",
                "email": "test_remove_user_from_api_group_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/v1/auth/login/",
            {"username": "test_remove_user_from_api_group", "password": "testpassword"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_remove_user_from_api_group",
                "email": "test@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_remove_user_from_api_group")
        assert group is not None
        assert group.name == "test_remove_user_from_api_group"
        assert group.admin_list.filter(
            username="test_remove_user_from_api_group"
        ).exists()
        response = client.post(
            "/v1/group/remove_user/",
            {
                "api_group_name": "test_remove_user_from_api_group",
                "username": "test_remove_user_from_api_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert not group.user_list.filter(
            username="test_remove_user_from_api_group_two"
        ).exists()

    def test_add_admin_to_api_group(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_add_admin_to_api_group",
                "password": "testpassword",
                "email": "test_add_admin_to_api_group@test.com",
            },
        )
        auth_response_two = client.post(
            "/v1/auth/register/",
            {
                "username": "test_add_admin_to_api_group_two",
                "password": "testpassword",
                "email": "test_add_admin_to_api_group_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/v1/auth/login/",
            {"username": "test_add_admin_to_api_group", "password": "testpassword"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_add_admin_to_api_group",
                "email": "test@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_add_admin_to_api_group")
        assert group is not None
        assert group.name == "test_add_admin_to_api_group"
        assert group.admin_list.filter(username="test_add_admin_to_api_group").exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_add_admin_to_api_group",
                "username": "test_add_admin_to_api_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_add_admin_to_api_group_two"
        ).exists()
        response = client.post(
            "/v1/group/add_admin/",
            {
                "api_group_name": "test_add_admin_to_api_group",
                "username": "test_add_admin_to_api_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.admin_list.filter(
            username="test_add_admin_to_api_group_two"
        ).exists()

    def test_add_admin_to_api_group_as_non_admin(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_add_admin_to_api_group_as_non_admin",
                "password": "testpassword",
                "email": "test_add_admin_to_api_group_as_non_admin@test.com",
            },
        )
        auth_response_two = client.post(
            "/v1/auth/register/",
            {
                "username": "test_add_admin_to_api_group_as_non_admin_two",
                "password": "testpassword",
                "email": "test_add_admin_to_api_group_as_non_admin_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/v1/auth/login/",
            {
                "username": "test_add_admin_to_api_group_as_non_admin",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        login_response_two = client.post(
            "/v1/auth/login/",
            {
                "username": "test_add_admin_to_api_group_as_non_admin_two",
                "password": "testpassword",
            },
        )
        assert login_response_two.status_code == 200
        token_two = login_response_two.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_add_admin_to_api_group_as_non_admin",
                "email": "test@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_add_admin_to_api_group_as_non_admin")
        assert group is not None
        assert group.admin_list.filter(
            username="test_add_admin_to_api_group_as_non_admin"
        ).exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_add_admin_to_api_group_as_non_admin",
                "username": "test_add_admin_to_api_group_as_non_admin_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_add_admin_to_api_group_as_non_admin_two"
        ).exists()
        response = client.post(
            "/v1/group/add_admin/",
            {
                "api_group_name": "test_add_admin_to_api_group_as_non_admin",
                "username": "test_add_admin_to_api_group_as_non_admin_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token_two}",
        )
        assert response.status_code == 200
        assert not group.admin_list.filter(
            username="test_add_admin_to_api_group_as_non_admin_two"
        ).exists()

    def test_add_admin_to_api_group_already_in_group(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_add_admin_to_api_group_already_in_group",
                "password": "testpassword",
                "email": "test_add_admin_to_api_group_already_in_group@test.com",
            },
        )
        auth_response_two = client.post(
            "/v1/auth/register/",
            {
                "username": "test_add_admin_to_api_group_already_in_group_two",
                "password": "testpassword",
                "email": "test_add_admin_to_api_group_already_in_group_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/v1/auth/login/",
            {
                "username": "test_add_admin_to_api_group_already_in_group",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_add_admin_to_api_group_already_in_group",
                "email": "test@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(
            name="test_add_admin_to_api_group_already_in_group"
        )
        assert group is not None
        assert group.admin_list.filter(
            username="test_add_admin_to_api_group_already_in_group"
        ).exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_add_admin_to_api_group_already_in_group",
                "username": "test_add_admin_to_api_group_already_in_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_add_admin_to_api_group_already_in_group_two"
        ).exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_add_admin_to_api_group_already_in_group",
                "username": "test_add_admin_to_api_group_already_in_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 400
        assert group.user_list.filter(
            username="test_add_admin_to_api_group_already_in_group_two"
        ).exists()

    def test_remove_admin_from_api_group(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_admin_from_api_group",
                "password": "testpassword",
                "email": "test_remove_admin_from_api_group@test.com",
            },
        )
        auth_response_two = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_admin_from_api_group_two",
                "password": "testpassword",
                "email": "test_remove_admin_from_api_group_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/v1/auth/login/",
            {
                "username": "test_remove_admin_from_api_group",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_remove_admin_from_api_group",
                "email": "test@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_remove_admin_from_api_group")
        assert group is not None
        assert group.admin_list.filter(
            username="test_remove_admin_from_api_group"
        ).exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_remove_admin_from_api_group",
                "username": "test_remove_admin_from_api_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_remove_admin_from_api_group_two"
        ).exists()
        response = client.post(
            "/v1/group/add_admin/",
            {
                "api_group_name": "test_remove_admin_from_api_group",
                "username": "test_remove_admin_from_api_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.admin_list.filter(
            username="test_remove_admin_from_api_group_two"
        ).exists()
        response = client.post(
            "/v1/group/remove_admin/",
            {
                "api_group_name": "test_remove_admin_from_api_group",
                "username": "test_remove_admin_from_api_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert not group.admin_list.filter(
            username="test_remove_admin_from_api_group_two"
        ).exists()

    def test_remove_admin_from_api_group_as_non_admin(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_admin_from_api_group_as_non_admin",
                "password": "testpassword",
                "email": "test_remove_admin_from_api_group_as_non_admin@test.com",
            },
        )
        auth_response_two = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_admin_from_api_group_as_non_admin_two",
                "password": "testpassword",
                "email": "test_remove_admin_from_api_group_as_non_admin_two@test.com",
            },
        )
        auth_response_three = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_admin_from_api_group_as_non_admin_three",
                "password": "testpassword",
                "email": "test_remove_admin_from_api_group_as_non_admin_three@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        assert auth_response_three.status_code == 200
        login_response = client.post(
            "/v1/auth/login/",
            {
                "username": "test_remove_admin_from_api_group_as_non_admin",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        token_three = auth_response_three.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_remove_admin_from_api_group_as_non_admin",
                "email": "test@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(
            name="test_remove_admin_from_api_group_as_non_admin"
        )
        assert group is not None
        assert group.admin_list.filter(
            username="test_remove_admin_from_api_group_as_non_admin"
        ).exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_remove_admin_from_api_group_as_non_admin",
                "username": "test_remove_admin_from_api_group_as_non_admin_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_remove_admin_from_api_group_as_non_admin_two"
        ).exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_remove_admin_from_api_group_as_non_admin",
                "username": "test_remove_admin_from_api_group_as_non_admin_three",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_remove_admin_from_api_group_as_non_admin_three"
        ).exists()
        response = client.post(
            "/v1/group/add_admin/",
            {
                "api_group_name": "test_remove_admin_from_api_group_as_non_admin",
                "username": "test_remove_admin_from_api_group_as_non_admin_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.admin_list.filter(
            username="test_remove_admin_from_api_group_as_non_admin_two"
        ).exists()
        response = client.post(
            "/v1/group/remove_admin/",
            {
                "api_group_name": "test_remove_admin_from_api_group_as_non_admin",
                "username": "test_remove_admin_from_api_group_as_non_admin_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token_three}",
        )
        assert response.status_code == 200
        assert group.admin_list.filter(
            username="test_remove_admin_from_api_group_as_non_admin_two"
        ).exists()

    def test_remove_admin_from_api_group_not_in_group(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_admin_from_api_group_not_in_group",
                "password": "testpassword",
                "email": "test_remove_admin_from_api_group_not_in_group@test.com",
            },
        )
        auth_response_two = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_admin_from_api_group_not_in_group_two",
                "password": "testpassword",
                "email": "test_remove_admin_from_api_group_not_in_group_two@test.com",
            },
        )
        auth_response_three = client.post(
            "/v1/auth/register/",
            {
                "username": "test_remove_admin_from_api_group_not_in_group_three",
                "password": "testpassword",
                "email": "test_remove_admin_from_api_group_not_in_group_three@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        assert auth_response_three.status_code == 200
        login_response = client.post(
            "/v1/auth/login/",
            {
                "username": "test_remove_admin_from_api_group_not_in_group",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        token_two = auth_response_two.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_remove_admin_from_api_group_not_in_group",
                "email": "test@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(
            name="test_remove_admin_from_api_group_not_in_group"
        )
        assert group is not None
        assert group.admin_list.filter(
            username="test_remove_admin_from_api_group_not_in_group"
        ).exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_remove_admin_from_api_group_not_in_group",
                "username": "test_remove_admin_from_api_group_not_in_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_remove_admin_from_api_group_not_in_group_two"
        ).exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_remove_admin_from_api_group_not_in_group",
                "username": "test_remove_admin_from_api_group_not_in_group_three",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(
            username="test_remove_admin_from_api_group_not_in_group_three"
        ).exists()
        response = client.post(
            "/v1/group/add_admin/",
            {
                "api_group_name": "test_remove_admin_from_api_group_not_in_group",
                "username": "test_remove_admin_from_api_group_not_in_group_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.admin_list.filter(
            username="test_remove_admin_from_api_group_not_in_group_two"
        ).exists()
        assert not group.admin_list.filter(
            username="test_remove_admin_from_api_group_not_in_group_three"
        ).exists()
        response = client.post(
            "/v1/group/remove_admin/",
            {
                "api_group_name": "test_remove_admin_from_api_group_not_in_group",
                "username": "test_remove_admin_from_api_group_not_in_group_three",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token_two}",
        )
        assert response.status_code == 200
        assert not group.admin_list.filter(
            username="test_remove_admin_from_api_group_not_in_group_three"
        ).exists()

    def test_get_api_group_users(self):
        client = Client()
        user_model = get_user_model()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_get_api_group_users",
                "password": "testpassword",
                "email": "test_get_api_group_users@test.com",
            },
        )
        auth_response_two = client.post(
            "/v1/auth/register/",
            {
                "username": "test_get_api_group_users_two",
                "password": "testpassword",
                "email": "test_get_api_group_users_two@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response_two.status_code == 200
        login_response = client.post(
            "/v1/auth/login/",
            {
                "username": "test_get_api_group_users",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        token_two = auth_response_two.json()["token"]
        UserKeys.objects.create(
            user=user_model.objects.get(username="test_get_api_group_users"),
            mnemonic="test_get_api_group_users",
        )
        UserKeys.objects.create(
            user=user_model.objects.get(username="test_get_api_group_users_two"),
            mnemonic="test_get_api_group_users_two",
        )
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_get_api_group_users",
                "email": "test_get_api_group_users@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_get_api_group_users")
        assert group is not None
        assert group.name == "test_get_api_group_users"
        assert group.admin_list.filter(username="test_get_api_group_users").exists()
        response = client.post(
            "/v1/group/add_user/",
            {
                "api_group_name": "test_get_api_group_users",
                "username": "test_get_api_group_users_two",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert group.user_list.filter(username="test_get_api_group_users_two").exists()
        response = client.post(
            "/v1/group/get_api_group_users/",
            {
                "api_group_name": "test_get_api_group_users",
                "api_key": group.api_key,
                "api_secret": group.api_secret,
            },
            HTTP_AUTHORIZATION=f"Token {token_two}",
        )
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["username"] == "test_get_api_group_users"
        assert response.json()[1]["username"] == "test_get_api_group_users_two"

    def test_get_api_group_list(self):
        client = Client()
        user_model = get_user_model()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_get_api_group_list",
                "password": "testpassword",
                "email": "test_get_api_group_list@test.com",
            },
        )
        user = user_model.objects.get(username="test_get_api_group_list")
        Group.objects.get_or_create(name="FennelAdmin")[0].user_set.add(user)
        assert auth_response.status_code == 200
        token = auth_response.json()["token"]
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_get_api_group_list",
                "email": "test_get_api_group_list@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        response = client.get(
            "/v1/group/get_list/",
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["api_group_name"] == "test_get_api_group_list"
