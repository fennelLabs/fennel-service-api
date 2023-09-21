from django.test import TestCase

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
