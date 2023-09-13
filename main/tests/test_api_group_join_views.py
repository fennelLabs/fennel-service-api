from django.test import Client, TestCase
from django.contrib.auth import get_user_model

from main.models import APIGroupJoinRequest, APIGroup, UserKeys


class TestAPIGroupJoinRequestViews(TestCase):
    def test_send_join_request(self):
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
        assert token is not None
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
            "/v1/group/send_join_request/",
            {
                "api_group_name": "test_get_api_group_users",
            },
            HTTP_AUTHORIZATION=f"Token {auth_response_two.json()['token']}",
        )
        assert response.status_code == 200
        assert APIGroupJoinRequest.objects.filter(
            api_group=group,
            user__username="test_get_api_group_users_two",
        ).exists()
        user_model.objects.all().delete()
        APIGroup.objects.all().delete()
        UserKeys.objects.all().delete()

    def test_get_api_group_join_requests(self):
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
        assert token is not None
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
            "/v1/group/send_join_request/",
            {
                "api_group_name": "test_get_api_group_users",
            },
            HTTP_AUTHORIZATION=f"Token {auth_response_two.json()['token']}",
        )
        assert response.status_code == 200
        assert APIGroupJoinRequest.objects.filter(
            api_group=group,
            user__username="test_get_api_group_users_two",
        ).exists()
        response = client.post(
            "/v1/group/get_join_requests/",
            {
                "api_group_name": "test_get_api_group_users",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        user_model.objects.all().delete()
        APIGroup.objects.all().delete()
        UserKeys.objects.all().delete()

    def test_get_api_group_join_requests_no_requests(self):
        client = Client()
        user_model = get_user_model()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test_get_api_group_join_requests",
                "password": "testpassword",
                "email": "test_get_api_group_join_requests@test.com",
            },
        )
        assert auth_response.status_code == 200
        token = auth_response.json()["token"]
        assert token is not None
        response = client.post(
            "/v1/group/create/",
            {
                "api_group_name": "test_get_api_group_join_requests",
                "email": "test_get_api_group_join_requests@test.com",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        group = APIGroup.objects.get(name="test_get_api_group_join_requests")
        assert group is not None
        assert group.name == "test_get_api_group_join_requests"
        assert group.admin_list.filter(
            username="test_get_api_group_join_requests"
        ).exists()
        response = client.post(
            "/v1/group/get_join_requests/",
            {
                "api_group_name": "test_get_api_group_join_requests",
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert len(response.json()) == 0
        user_model.objects.all().delete()
        APIGroup.objects.all().delete()

    def test_accept_join_request(self):
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
        assert token is not None
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
            "/v1/group/send_join_request/",
            {
                "api_group_name": "test_get_api_group_users",
            },
            HTTP_AUTHORIZATION=f"Token {auth_response_two.json()['token']}",
        )
        assert response.status_code == 200
        group_request = APIGroupJoinRequest.objects.get(
            api_group=group,
            user__username="test_get_api_group_users_two",
        )
        response = client.post(
            "/v1/group/accept_join_request/",
            {
                "join_request_id": group_request.id,
            },
            HTTP_AUTHORIZATION=f"Token {token}",
        )
        assert response.status_code == 200
        assert not APIGroupJoinRequest.objects.filter(
            api_group=group,
            user__username="test_get_api_group_users_two",
        ).exists()
        assert group.user_list.filter(username="test_get_api_group_users_two").exists()
        user_model.objects.all().delete()
        APIGroup.objects.all().delete()
        UserKeys.objects.all().delete()
