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
        result, success = decode(signal_text, None, None)
        assert success
        assert result["prefix"] == "WF"
        assert result["version"] == "1"
        assert result["encryptionIndicator"] == "0"

    def test_decode_encrypted(self):
        signal_text = "574631312af34c38e3af3ab687ac276965c11b369274da9ddf514bcc0eebf037a268f087f3bda708026b5f7a5b83e49072a2d32f83bc283c249601066c488a0a1e40bb4f27dcb409c14aa7c7b7f0f656c9bc184a8df6fbe7928a25d3e5b74a81ab16df93efcc30b1105c7ba56878afed34f318d337532a293b41c7b54d1af2c6b92414a79e68077655f7e3629bf93b2f43e553ebd518198c2cc1a782bcc3d37e1304f431c9997c803368f54ef2f2774f42543c32d"
        result, success = decode(signal_text, None, None)
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
        assert response.json()[0]["signal_body"]["prefix"] == "WF"
        assert response.json()[0]["signal_body"]["version"] == "1"
        assert response.json()[0]["signal_body"]["encryptionIndicator"] == "0"

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
        assert response.json()[0]["signal_body"]["prefix"] == "WF"
        assert response.json()[0]["signal_body"]["version"] == "1"
        assert response.json()[0]["signal_body"]["encryptionIndicator"] == "1"

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
            {"signal": "Test."},
            {"signal": "Test."},
            {"signal": "Test."},
            {"signal": "Test."},
            {"signal": "Test."},
        ]
        response = client.post(
            "/v1/fennel/send_signal_list/",
            {"signals": signals_list},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_decode_list_with_errors_from_production(self):
        signal_text_list = [
            "5746313024a0000000000000000000000000000000000000000000000000000000000000000001011848b0290a480000011501204c41000262000000000000",
            "5746313024a0000000000000000000000000000000000000000000000000000000000000000291011848300a984800000114880a45a0f12f0cc00000000000",
            "5746313024a0000000000000000000000000000000000000000000000000000000000000000291011848308a91000000011418514ca0640503200000000000",
            "This is a test signal.",
            "5746313024a000000",
            "57",
            "5746313024a00000000000000000000000000000000000000000000000000000000000000002910118480849b84800000114e4245102400706000000000000",
            "<html><head><title>502 Bad Gateway</title></head><body><center><h1>502 Bad Gateway</h1></center><hr><center>nginx/1.18.0</center></body></html>",
            "5746313024a000000000000000000000000000000000000000000000000000000000000000029101184808820aa800000114e4245102400706000000000000",
            "5746313120800000000000000000000000000000000000000000000000000000000000000000b43a3a38399d1797b7b933b0b734b9b0ba34b7b71734b73a17bbb434ba32b33630b380",
            "5746313024a00000000000000000000000000000000000000000000000000000000000000002910118480849b84800000114e4245102400706000000000000",
            "{message: This is a test message}",
            "5746313120800000000000000000000000000000000000000000000000000000000000000000b43a3a38399d1797b7b933b0b734b9b0ba34b7b71734b73a17bbb434ba32b33630b380",
            "5746313024a0000000000000000000000000000000000000000000000000000000000000000291011840a08a38a000000115460c1da0092e30400000000000",
            "5746313024a0000000000000000000000000000000000000000000000000000000000000000291011840a01910c000000114dc2409012ae251200000000000",
            "5746313024a0000000000000000000000000000000000000000000000000000000000000000291011840b0188aa000000115460c1de0092e30600000000000",
            "5746313024a0000000000000000000000000000000000000000000000000000000000000000291011841804922a80000011546095020092e4ca00000000000",
            "<html>\r\n<head><title>502 Bad Gateway</title></head>\r\n<body>\r\n<center><h1>502 Bad Gateway</h1></center>\r\n<hr><center>nginx/1.18.0</center>\r\n</body>\r\n</html>",
            "5746313024a00000000000000000000000000000000000000000000000000000000000000002910118480881290000000114e4245102400706000000000000",
            "5746313024a00000000000000000000000000000000000000000000000000000000000000002910118480881290000000114e4245102400706000000000000",
            "5746313024a00000000000000000000000000000000000000000000000000000000000000002910118480881290000000114e4245102400706000000000000",
            "5746313024a000000000000000000000000000000000000000000000000000000000000000029101184808820aa800000114e4245102400706000000000000",
            "5746313024a000000000000000000000000000000000000000000000000000000000000000029101184808820aa800000114e4245102400706000000000000",
            "5746313024a00000000000000000000000000000000000000000000000000000000000000002910118480881290000000114e4245102400706000000000000",
            "5746313024a00000000000000000000000000000000000000000000000000000000000000002910118480849b84800000114e4245102400706000000000000",
            "5746313024a00000000000000000000000000000000000000000000000000000000000000002910118480849b84800000114e4245102400706000000000000",
            "5746313024a00000000000000000000000000000000000000000000000000000000000000002910118480849b84800000114e4245102400706000000000000",
        ]
        for signal_text in signal_text_list:
            Signal.objects.create(
                signal_text=signal_text,
            )
        signal_ids_list = [signal.id for signal in Signal.objects.all()]
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
            {"signals": signal_ids_list},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200

    def test_decode_list_with_wrong_body(self):
        Signal.objects.create(
            signal_text="57463130231874028bb2cce2270447493f0d319969b732100c46a5311f65e6cd13d8a73145c1bb119191b329b189b321b1a991919b099191a321b189b191b9a9b329b9c99181a981b991b1c9b321b189b991b9c99181a999b199b1c1b331b331b3199181a329b1b9b331b3119191bb20",
            signal_body="{'prefix': 'WF', 'version': '1', 'encryptionIndicator': '0', 'duressIndicator': '0', 'messageCode': 'F', 'referenceIndicator': '3', 'referencedMessage': '0e805176599c44e088e927e1a6332d36e6420188d4a623ecbcd9a27b14e628b8', 'text': '{\"name\":\"Mabuny Primary School Ngok\"}'}",
        )
        signal_ids_list = [signal.id for signal in Signal.objects.all()]
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
            {"signals": signal_ids_list},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
