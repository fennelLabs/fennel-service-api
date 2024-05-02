from django.test import Client, TestCase
from django.contrib.auth import get_user_model

from model_bakery import baker

from main.models import Signal, UserKeys


class TestReferenceMessages(TestCase):
    def test_breaking_referenced_message(self):
        client = Client()
        user_model = get_user_model()
        auth_response = client.post(
            "/api/v1/auth/register/",
            {
                "username": "breaking_referenced_message_test",
                "password": "test",
                "email": "breaking_referenced_message_test@test.com",
            },
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["token"] is not None
        user = user_model.objects.get(username="breaking_referenced_message_test")
        reference_signals = [
            Signal.objects.create(
                signal_text="5746313120800000000000000000000000000000000000000000000000000000000000000000b43a3a38399d1797b7b933b0b734b9b0ba34b7b71734b73a17bbb434ba32b33630b380"
            ),
            Signal.objects.create(
                signal_text="Request body deserialize error: invalid type: map, expected a string at line 1 column 180"
            ),
            Signal.objects.create(signal_text="57"),
            Signal.objects.create(
                signal_text="<html><head><title>502 Bad Gateway</title></head><body><center><h1>502 Bad Gateway</h1></center><hr><center>nginx/1.18.0</center></body></html>"
            ),
            Signal.objects.create(signal_text="5746313024a000000"),
            Signal.objects.create(signal_text="{message: this is a test message}"),
            Signal.objects.create(signal_text="{'message': 'this is a test message'}"),
            baker.make(Signal),
            baker.make(Signal),
            baker.make(Signal),
        ]
        signal = Signal.objects.create(
            signal_text="5746313120800000000000000000000000000000000000000000000000000000000000000000b43a3a38399d1797b7b933b0b734b9b0ba34b7b71734b73a17bbb434ba32b33630b380",
        )
        signal.references.set(reference_signals)
        signal.save()
        baker.make(UserKeys, user=user)
        response = client.post(
            "/api/v1/whiteflag/decode_list/",
            {"signals": signal.id},
            HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
