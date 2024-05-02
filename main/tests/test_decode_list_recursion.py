from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from model_bakery import baker

from main.models import Signal, UserKeys


class TestDecodeListRecursion(TestCase):
    def test_recursion_error_fix_oct_24(self):
        client = Client()
        user_model = get_user_model()
        response = client.post(
            "/api/v1/auth/register/",
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
                tx_hash="3efb4e6e4a33122b242634254c1920a769d615dfcc4c670bb53eb6f12843c3ae",
                sender=user,
                signal_text="57463130a4a1f7da7067d41891592131a12a60c9053b4eb0aefe6263385da9f5b789421e1d7401009841882148a800000114c1e596006f04c050eca6420084",
            ),
            baker.make(
                Signal,
                tx_hash="3efb4e0cfa83122b242634254c1920a769d615dfcc4c670bb53eb6f12843c3ae",
                sender=user,
                signal_text="57463130a4a1f7da7372519891592131a12a60c9053b4eb0aefe6263385da9f5b789421e1d7401009841882148a800000114c1e596006f04c050eca6420084",
            ),
        ]
        signals_list = [signal.id for signal in signals]
        response = client.post(
            "/api/v1/whiteflag/decode_list/",
            {"signals": signals_list},
            HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
        )
        assert response.status_code == 200
