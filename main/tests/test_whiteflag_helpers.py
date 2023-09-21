from django.test import Client, TestCase

from django.contrib.auth import get_user_model

from main.models import APIGroup
from main.whiteflag_helpers import generate_diffie_hellman_keys, generate_shared_secret


class TestWhiteflagHelpers(TestCase):
    def test_generate_shared_secret(self):
        keys_dict_one = generate_diffie_hellman_keys()
        assert keys_dict_one["success"]
        keys_dict_two = generate_diffie_hellman_keys()
        assert keys_dict_two["success"]
        group_1 = APIGroup.objects.create(
            name="test group 1",
            email="test@test.com",
            public_diffie_hellman_key=keys_dict_one["public_key"],
            private_diffie_hellman_key=keys_dict_one["secret_key"],
        )
        group_2 = APIGroup.objects.create(
            name="test group 2",
            email="test2@test.com",
            public_diffie_hellman_key=keys_dict_two["public_key"],
            private_diffie_hellman_key=keys_dict_two["secret_key"],
        )
        shared_secret_one, success = generate_shared_secret(group_1, group_2)
        assert success
        assert shared_secret_one is not None
        shared_secret_two, success = generate_shared_secret(group_2, group_1)
        assert success
        assert shared_secret_two is not None
        assert shared_secret_one == shared_secret_two

    def test_generate_shared_secret_with_invalid_keys(self):
        keys_dict_one = generate_diffie_hellman_keys()
        assert keys_dict_one["success"]
        group_1 = APIGroup.objects.create(
            name="test group 1",
            email="test@test.com",
            public_diffie_hellman_key=keys_dict_one["public_key"],
            private_diffie_hellman_key=keys_dict_one["secret_key"],
        )
        shared_secret_one, success = generate_shared_secret(group_1, group_1)
        assert success
        assert shared_secret_one is not None

    def test_whiteflag_generate_shared_secret_key(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test",
                "password": "test",
                "email": "test@test.com",
            },
        )
        user_model = get_user_model()
        user = user_model.objects.get(username="test")
        keys_dict_one = generate_diffie_hellman_keys()
        keys_dict_two = generate_diffie_hellman_keys()
        group_1 = APIGroup.objects.create(
            name="test group 1",
            email="test@test.com",
            public_diffie_hellman_key=keys_dict_one["public_key"],
            private_diffie_hellman_key=keys_dict_one["secret_key"],
        )
        group_1.user_list.add(user)
        group_2 = APIGroup.objects.create(
            name="test group 2",
            email="test2@test.com",
            public_diffie_hellman_key=keys_dict_two["public_key"],
            private_diffie_hellman_key=keys_dict_two["secret_key"],
        )
        response = client.post(
            f"/v1/whiteflag/generate_encryption_key/{group_2.id}/",
            HTTP_AUTHORIZATION=f"Token {auth_response.data['token']}",
        )
        assert response.status_code == 200
        assert response.data["success"]
        assert response.data["shared_secret"] is not None
