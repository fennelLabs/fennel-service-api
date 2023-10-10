from django.test import Client, TestCase
from main.models import APIGroup


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
