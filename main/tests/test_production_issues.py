from django.test import Client, TestCase
from main.models import APIGroup
from main.whiteflag_helpers import whiteflag_encoder_helper


class TestProductionIssues(TestCase):
    def test_no_attribute_recipient_group_in_send_new_signal(self):
        client = Client()
        auth_response = client.post(
            "/v1/auth/register/",
            {
                "username": "test",
                "password": "test",
                "email": "test@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["token"] is not None
        client.post(
            "/v1/fennel/create_account/",
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        APIGroup.objects.create(
            name="testapirodney",
        )
        payload = {
            "signal": "5746313024a000000000000000000000000000000000000000000000000000000000000000029101188080188a2000000115460461600ae2caa00000000000",
            "recipient_group": "testapirodney",
        }
        response = client.post(
            "/v1/fennel/send_new_signal/",
            payload,
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        assert response.status_code == 400

    def test_annotation_encode_with_breaking_message(self):
        annotations_signal = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "F",
            "text": "Test",
            "referenceIndicator": "3",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }
        _, annotation_encode_success = whiteflag_encoder_helper(
            annotations_signal, None, None
        )
        assert annotation_encode_success
        annotations_signal = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "F",
            "text": '{"name":"School name"}',
            "referenceIndicator": "3",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }
        _, annotation_encode_success = whiteflag_encoder_helper(
            annotations_signal, None, None
        )
        assert annotation_encode_success
