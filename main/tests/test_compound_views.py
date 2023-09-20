import json

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth import get_user_model

from model_bakery import baker

from main.models import Signal, UserKeys
from main.whiteflag_helpers import decode


class TestCompoundViews(TestCase):
    def test_decode_not_encrypted(self):
        signal_text = "5746313020a00000000000000000000000000000000000000000000000000000000000000000b43a3a38399d1797b7b933b0b734b9b0ba34b7b71734b73a17bbb434ba32b33630b380"
        result, success = decode(signal_text)
        assert success
        assert result["prefix"] == "WF"
        assert result["version"] == "1"
        assert result["encryptionIndicator"] == "0"

    def test_decode_encrypted(self):
        signal_text = "574631312af34c38e3af3ab687ac276965c11b369274da9ddf514bcc0eebf037a268f087f3bda708026b5f7a5b83e49072a2d32f83bc283c249601066c488a0a1e40bb4f27dcb409c14aa7c7b7f0f656c9bc184a8df6fbe7928a25d3e5b74a81ab16df93efcc30b1105c7ba56878afed34f318d337532a293b41c7b54d1af2c6b92414a79e68077655f7e3629bf93b2f43e553ebd518198c2cc1a782bcc3d37e1304f431c9997c803368f54ef2f2774f42543c32d"
        result, success = decode(signal_text)
        assert success
        assert result["prefix"] == "WF"
        assert result["version"] == "1"
        assert result["encryptionIndicator"] == "1"
        assert (
            result["signal_body"]
            == "2af34c38e3af3ab687ac276965c11b369274da9ddf514bcc0eebf037a268f087f3bda708026b5f7a5b83e49072a2d32f83bc283c249601066c488a0a1e40bb4f27dcb409c14aa7c7b7f0f656c9bc184a8df6fbe7928a25d3e5b74a81ab16df93efcc30b1105c7ba56878afed34f318d337532a293b41c7b54d1af2c6b92414a79e68077655f7e3629bf93b2f43e553ebd518198c2cc1a782bcc3d37e1304f431c9997c803368f54ef2f2774f42543c32d"
        )

    def test_decode_list_not_encrypted(self):
        client = Client()
        user_model = get_user_model()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "decode_list_test",
                "password": "test",
                "email": "decode_list_test@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        user = user_model.objects.get(username="decode_list_test")
        baker.make(UserKeys, user=user)
        signal = baker.make(
            Signal,
            sender=user,
            signal_text="5746313020a00000000000000000000000000000000000000000000000000000000000000000b43a3a38399d1797b7b933b0b734b9b0ba34b7b71734b73a17bbb434ba32b33630b380",
        )
        response = client.post(
            "/v1/whiteflag/decode_list/",
            {"signals": [signal.id]},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
        assert response.json()[0]["id"] == signal.id
        assert response.json()[0]["signal_text"]["prefix"] == "WF"
        assert response.json()[0]["signal_text"]["version"] == "1"
        assert response.json()[0]["signal_text"]["encryptionIndicator"] == "0"

    def test_decode_list_encrypted(self):
        client = Client()
        user_model = get_user_model()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "decode_list_test",
                "password": "test",
                "email": "decode_list_test@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        user = user_model.objects.get(username="decode_list_test")
        baker.make(UserKeys, user=user)
        signal = baker.make(
            Signal,
            sender=user,
            signal_text="574631312af34c38e3af3ab687ac276965c11b369274da9ddf514bcc0eebf037a268f087f3bda708026b5f7a5b83e49072a2d32f83bc283c249601066c488a0a1e40bb4f27dcb409c14aa7c7b7f0f656c9bc184a8df6fbe7928a25d3e5b74a81ab16df93efcc30b1105c7ba56878afed34f318d337532a293b41c7b54d1af2c6b92414a79e68077655f7e3629bf93b2f43e553ebd518198c2cc1a782bcc3d37e1304f431c9997c803368f54ef2f2774f42543c32d",
        )
        response = client.post(
            "/v1/whiteflag/decode_list/",
            {"signals": [signal.id]},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
        assert response.json()[0]["id"] == signal.id
        assert response.json()[0]["signal_text"]["prefix"] == "WF"
        assert response.json()[0]["signal_text"]["version"] == "1"
        assert response.json()[0]["signal_text"]["encryptionIndicator"] == "1"

    def test_decode_long_signal_list(self):
        client = Client()
        user_model = get_user_model()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "decode_long_list_test",
                "password": "test",
                "email": "decode_long_list_test@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        user = user_model.objects.get(username="decode_long_list_test")
        baker.make(UserKeys, user=user)
        signals = [
            baker.make(
                Signal,
                sender=user,
                signal_text="574631312af34c38e3af3ab687ac276965c11b369274da9ddf514bcc0eebf037a268f087f3bda708026b5f7a5b83e49072a2d32f83bc283c249601066c488a0a1e40bb4f27dcb409c14aa7c7b7f0f656c9bc184a8df6fbe7928a25d3e5b74a81ab16df93efcc30b1105c7ba56878afed34f318d337532a293b41c7b54d1af2c6b92414a79e68077655f7e3629bf93b2f43e553ebd518198c2cc1a782bcc3d37e1304f431c9997c803368f54ef2f2774f42543c32d",
            )
            for _ in range(100)
        ]
        signals_list = [signal.id for signal in signals]
        response = client.post(
            "/v1/whiteflag/decode_list/",
            {"signals": signals_list},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
        assert len(response.json()) == 100

    def test_decode_list_with_non_whiteflag_signals(self):
        client = Client()
        user_model = get_user_model()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "decode_list_with_non_whiteflag_signals_test",
                "password": "test",
                "email": "decode_list_with_non_whiteflag_signals@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        user = user_model.objects.get(
            username="decode_list_with_non_whiteflag_signals_test"
        )
        baker.make(UserKeys, user=user)
        baker.make(
            Signal,
            sender=user,
            signal_text="574631312af34c38e3af3ab687ac276965c11b369274da9ddf514bcc0eebf037a268f087f3bda708026b5f7a5b83e49072a2d32f83bc283c249601066c488a0a1e40bb4f27dcb409c14aa7c7b7f0f656c9bc184a8df6fbe7928a25d3e5b74a81ab16df93efcc30b1105c7ba56878afed34f318d337532a293b41c7b54d1af2c6b92414a79e68077655f7e3629bf93b2f43e553ebd518198c2cc1a782bcc3d37e1304f431c9997c803368f54ef2f2774f42543c32d",
        )
        baker.make(
            Signal,
            sender=user,
            signal_text="This is not a whiteflag signal",
        )
        response = client.post(
            "/v1/whiteflag/decode_list/",
            {"signals": [signal.id for signal in Signal.objects.all()]},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_decode_list_does_not_exist(self):
        client = Client()
        user_model = get_user_model()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "decode_list_does_not_exist_test",
                "password": "test",
                "email": "decode_list_does_not_exist_test@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        user = user_model.objects.get(username="decode_list_does_not_exist_test")
        baker.make(UserKeys, user=user)
        response = client.post(
            "/v1/whiteflag/decode_list/",
            {"signals": [0]},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 400

    def test_decode_list_empty_input(self):
        client = Client()
        user_model = get_user_model()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "decode_list_empty_input_test",
                "password": "test",
                "email": "decode_list_empty_input_test@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        user = user_model.objects.get(username="decode_list_empty_input_test")
        baker.make(UserKeys, user=user)
        response = client.post(
            "/v1/whiteflag/decode_list/",
            {"signals": []},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 400

    def test_decode_list_with_reference_messages_and_confirmations(self):
        client = Client()
        user_model = get_user_model()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "decode_list_with_reference_messages_test",
                "password": "test",
                "email": "decode_list_with_reference_messages_test@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["token"] is not None
        user = user_model.objects.get(
            username="decode_list_with_reference_messages_test"
        )
        baker.make(UserKeys, user=user)
        encode_response = client.post(
            "/v1/whiteflag/encode/",
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
            },
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        assert encode_response.status_code == 200
        assert encode_response.json() is not None
        assert encode_response.json() != ""
        signal = baker.make(
            Signal,
            sender=user,
            signal_text=encode_response.json(),
            tx_hash="3efb4e0cfa83122b242634254c1920a769d615dfcc4c670bb53eb6f12843c3ae",
        )
        encode_response2 = client.post(
            "/v1/whiteflag/encode/",
            {
                "encryptionIndicator": "0",
                "duressIndicator": "0",
                "messageCode": "I",
                "referenceIndicator": "4",
                "referencedMessage": signal.tx_hash,
                "subjectCode": "52",
                "dateTime": "2023-09-01T09:37:09Z",
                "duration": "P00D00H00M",
                "objectType": "22",
                "objectLatitude": "+39.09144",
                "objectLongitude": "-120.03830",
                "objectSizeDim1": "0000",
                "objectSizeDim2": "0000",
                "objectOrientation": "000",
            },
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        assert encode_response2.status_code == 200
        assert encode_response2.json() is not None
        assert encode_response2.json() != ""
        signal2 = baker.make(
            Signal,
            sender=user,
            signal_text=encode_response2.json(),
            tx_hash="TEST2",
        )
        baker.make(
            "main.ConfirmationRecord",
            signal=signal2,
            confirmer=user,
        )
        response = client.post(
            "/v1/whiteflag/decode_list/",
            {"signals": [signal.id, signal2.id]},
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        assert response.status_code == 200
        assert response.json()[1]["id"] == signal2.id
        assert response.json()[1]["references"][0]["id"] == signal.id
        assert response.json()[1]["references"][0]["tx_hash"] == signal.tx_hash
        assert response.json()[1]["confirmations"][0]["id"] is not None
        assert response.json()[1]["confirmations"][0]["signal"] == signal2.id
        assert response.json()[1]["confirmations"][0]["confirmer"] == user.id

    def test_get_fee_for_send_signal_with_annotations(self):
        client = Client()
        user_model = get_user_model()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "send_signal_with_annotations_test",
                "password": "test",
                "email": "send_signal_with_annotations_test@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["token"] is not None
        user = user_model.objects.get(username="send_signal_with_annotations_test")
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
            ),
            "annotations": '{"test": "test"}',
        }
        response = client.post(
            "/v1/whiteflag/get_fee_for_send_signal_with_annotations/",
            payload,
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        assert response.status_code == 200
        assert response.json()["signal_response"]["fee"] is not None
        assert response.json()["annotation_response"]["fee"] is not None
        assert response.json()["total_fee"] is not None

    def test_send_signal_with_annotations(self):
        client = Client()
        user_model = get_user_model()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "send_signal_with_annotations_test",
                "password": "test",
                "email": "send_signal_with_annotations_test@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["token"] is not None
        user = user_model.objects.get(username="send_signal_with_annotations_test")
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
            ),
            "annotations": '{"test": "test"}',
        }
        response = client.post(
            "/v1/whiteflag/send_signal_with_annotations/",
            payload,
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        assert response.status_code == 400
        assert response.json()["signal_id"] is not None
        assert response.json()["fee"] is not None

    def test_encode_list(self):
        client = Client()
        user_model = get_user_model()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "encode_list_test",
                "password": "test",
                "email": "encode_list_test@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        user = user_model.objects.get(username="encode_list_test")
        baker.make(UserKeys, user=user)
        signals_list = [
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
        ]
        response = client.post(
            "/v1/whiteflag/encode_list/",
            {"signals": signals_list},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_fee_for_send_signal_list(self):
        client = Client()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "get_fee_for_send_signal_list_test",
                "password": "test",
                "email": "get_fee_for_send_signal_list_test@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        client.post(
            "/v1/fennel/create_account/",
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        signals_list = [
            "Test.",
            "Test.",
            "Test.",
            "Test.",
            "Test.",
        ]
        response = client.post(
            "/v1/fennel/get_fee_for_send_signal_list/",
            {"signals": signals_list},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
        assert response.json()["signals"][0]["fee"] is not None
        assert response.json()["total_fee"] is not None
        assert response.json()["total_fee"] == (
            response.json()["signals"][0]["fee"]
            + response.json()["signals"][1]["fee"]
            + response.json()["signals"][2]["fee"]
            + response.json()["signals"][3]["fee"]
            + response.json()["signals"][4]["fee"]
        )

    def test_send_signal_list(self):
        client = Client()
        response = client.post(
            "/v1/auth/register/",
            {
                "username": "send_signal_list_test",
                "password": "test",
                "email": "send_signal_list_test@test.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["token"] is not None
        client.post(
            "/v1/fennel/create_account/",
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        signals_list = [
            "Test.",
            "Test.",
            "Test.",
            "Test.",
            "Test.",
        ]
        response = client.post(
            "/v1/fennel/send_signal_list/",
            {"signals": signals_list},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
        assert len(response.json()) == 5
