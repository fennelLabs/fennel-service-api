import json

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth import get_user_model

from main.models import APIGroup, UserKeys


class TestEncodeAndSendViews(TestCase):
    def test_get_fee_for_encode_and_send_signal(self):
        client = Client()
        user_model = get_user_model()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "encode_and_send_signal_test",
                "password": "test",
                "email": "encode_and_send_signal_test@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["token"] is not None
        user = user_model.objects.get(username="encode_and_send_signal_test")
        client.post(
            "/v1/fennel/create_account/",
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        user_keys = UserKeys.objects.get(user=user)
        user_keys.balance = "1000000000"
        user_keys.save()
        payload = {
            "signal_body": json.dumps(
                {
                    "encryptionIndicator": "0",
                    "duressIndicator": "0",
                    "messageCode": "I",
                    "referenceIndicator": "4",
                    "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
                    "subjectCode": "52",
                    "dateTime": "2023-09-01T09:37:09Z",
                    "duration": "P00D00H00M",
                    "objectType": "22",
                    "objectLatitude": "+39.09144",
                    "objectLongitude": "-120.03830",
                    "objectSizeDim1": "0000",
                    "objectSizeDim2": "0000",
                    "objectOrientation": "000",
                }
            )
        }
        response = client.post(
            "/v1/whiteflag/get_fee_for_encode_and_send_signal/",
            payload,
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        assert response.status_code == 200
        assert response.json()["signal_response"]["fee"] is not None

    def test_encode_and_send_signal(self):
        client = Client()
        user_model = get_user_model()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "encode_and_send_signal_test",
                "password": "test",
                "email": "encode_and_send_signal_test@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["token"] is not None
        user = user_model.objects.get(username="encode_and_send_signal_test")
        client.post(
            "/v1/fennel/create_account/",
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        user_keys = UserKeys.objects.get(user=user)
        user_keys.balance = "1000000000"
        user_keys.save()
        payload = {
            "signal_body": json.dumps(
                {
                    "encryptionIndicator": "0",
                    "duressIndicator": "0",
                    "messageCode": "I",
                    "referenceIndicator": "4",
                    "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
                    "subjectCode": "52",
                    "dateTime": "2023-09-01T09:37:09Z",
                    "duration": "P00D00H00M",
                    "objectType": "22",
                    "objectLatitude": "+39.09144",
                    "objectLongitude": "-120.03830",
                    "objectSizeDim1": "0000",
                    "objectSizeDim2": "0000",
                    "objectOrientation": "000",
                }
            )
        }
        response = client.post(
            "/v1/whiteflag/encode_and_send_signal/",
            payload,
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        assert response.status_code == 400

    def test_encode_and_send_signal_with_recipient_group(self):
        client = Client()
        user_model = get_user_model()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "encode_and_send_signal_test",
                "password": "test",
                "email": "encode_and_send_signal_test@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["token"] is not None
        user = user_model.objects.get(username="encode_and_send_signal_test")
        client.post(
            "/v1/fennel/create_account/",
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        group = APIGroup.objects.create(
            name="test_group",
        )
        group.user_list.add(user)
        user_keys = UserKeys.objects.get(user=user)
        user_keys.balance = "1000000000"
        user_keys.save()
        payload = {
            "signal_body": json.dumps(
                {
                    "encryptionIndicator": "0",
                    "duressIndicator": "0",
                    "messageCode": "I",
                    "referenceIndicator": "4",
                    "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
                    "subjectCode": "52",
                    "dateTime": "2023-09-01T09:37:09Z",
                    "duration": "P00D00H00M",
                    "objectType": "22",
                    "objectLatitude": "+39.09144",
                    "objectLongitude": "-120.03830",
                    "objectSizeDim1": "0000",
                    "objectSizeDim2": "0000",
                    "objectOrientation": "000",
                }
            ),
            "recipient_group": "test_group",
        }
        response = client.post(
            "/v1/whiteflag/encode_and_send_signal/",
            payload,
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        assert response.status_code == 400
