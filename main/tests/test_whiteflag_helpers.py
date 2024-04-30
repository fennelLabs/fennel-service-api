from django.test import Client, TestCase

from django.contrib.auth import get_user_model

from main.models import APIGroup
from main.whiteflag_helpers import (
    generate_diffie_hellman_keys,
    generate_shared_secret,
    whiteflag_encoder_helper,
    decode,
)


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

    def test_encode_free_text_whiteflag_message_partial(self):
        message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "F",
            "text": "Test Message",
            "referenceIndicator": "3",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }
        encoded_message, success = whiteflag_encoder_helper(message)
        assert success
        assert encoded_message is not None

    def test_encode_free_text_whiteflag_message_string(self):
        message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "1",
            "messageCode": "F",
            "text": "This is a test.",
            "referenceIndicator": "3",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }
        encoded_message, success = whiteflag_encoder_helper(message)
        assert success
        assert encoded_message is not None

    def test_encode_free_text_whiteflag_message(self):
        message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "1",
            "messageCode": "F",
            "text": '{"test": "test"}',
            "referenceIndicator": "3",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }
        encoded_message, success = whiteflag_encoder_helper(message)
        assert success
        assert encoded_message is not None
        decoded_message, success = decode(encoded_message)
        assert success
        assert decoded_message is not None

    def test_decode_encrypted_whiteflag_message(self):
        keys_dict_one = generate_diffie_hellman_keys()
        keys_dict_two = generate_diffie_hellman_keys()
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
        message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "1",
            "duressIndicator": "1",
            "messageCode": "I",
            "referenceIndicator": "4",
            "referencedMessage": "3efb4e0cfa83122b242634254c1920a769d615dfcc4c670bb53eb6f12843c3ae",
            "subjectCode": "80",
            "datetime": "2013-08-31T04:29:15Z",
            "duration": "P00D00H00M",
            "objectType": "22",
            "objectLatitude": "+30.79658",
            "objectLongitude": "-037.82602",
            "objectSizeDim1": "8765",
            "objectSizeDim2": "3210",
            "objectOrientation": "042",
        }
        encoded_message, success = whiteflag_encoder_helper(message, group_1, group_2)
        assert success
        assert encoded_message is not None
        decoded_message, success = decode(encoded_message, group_1, group_2)
        assert success
        assert decoded_message is not None
        assert decoded_message["prefix"] == "WF"
        assert decoded_message["version"] == "1"
        assert decoded_message["encryptionIndicator"] == "1"
        assert decoded_message["duressIndicator"] == "1"
        assert decoded_message["messageCode"] == "I"
        assert decoded_message["referenceIndicator"] == "4"
        assert (
            decoded_message["referencedMessage"]
            == "3efb4e0cfa83122b242634254c1920a769d615dfcc4c670bb53eb6f12843c3ae"
        )
        assert decoded_message["subjectCode"] == "80"
        assert decoded_message["dateTime"] == "2013-08-31T04:29:15Z"
        assert decoded_message["duration"] == "P00D00H00M"
        assert decoded_message["objectType"] == "22"
        assert decoded_message["objectLatitude"] == "+30.79658"
        assert decoded_message["objectLongitude"] == "-037.82602"
        assert decoded_message["objectSizeDim1"] == "8765"
        assert decoded_message["objectSizeDim2"] == "3210"
        assert decoded_message["objectOrientation"] == "042"
