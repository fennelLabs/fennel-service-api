from django.test.client import Client
from django.contrib.auth import get_user_model
from main.models import Signal, UserKeys
from model_bakery import baker
from main.compound_views import __decode


def test_decode_not_encrypted():
    signal_text = "5746313020a00000000000000000000000000000000000000000000000000000000000000000b43a3a38399d1797b7b933b0b734b9b0ba34b7b71734b73a17bbb434ba32b33630b380"
    result = __decode(signal_text)
    assert result["prefix"] == "WF"
    assert result["version"] == "1"
    assert result["encryptionIndicator"] == "0"


def test_decode_encrypted():
    signal_text = "574631312af34c38e3af3ab687ac276965c11b369274da9ddf514bcc0eebf037a268f087f3bda708026b5f7a5b83e49072a2d32f83bc283c249601066c488a0a1e40bb4f27dcb409c14aa7c7b7f0f656c9bc184a8df6fbe7928a25d3e5b74a81ab16df93efcc30b1105c7ba56878afed34f318d337532a293b41c7b54d1af2c6b92414a79e68077655f7e3629bf93b2f43e553ebd518198c2cc1a782bcc3d37e1304f431c9997c803368f54ef2f2774f42543c32d"
    result = __decode(signal_text)
    assert result["prefix"] == "WF"
    assert result["version"] == "1"
    assert result["encryptionIndicator"] == "1"
    assert (
        result["signal_body"]
        == "2af34c38e3af3ab687ac276965c11b369274da9ddf514bcc0eebf037a268f087f3bda708026b5f7a5b83e49072a2d32f83bc283c249601066c488a0a1e40bb4f27dcb409c14aa7c7b7f0f656c9bc184a8df6fbe7928a25d3e5b74a81ab16df93efcc30b1105c7ba56878afed34f318d337532a293b41c7b54d1af2c6b92414a79e68077655f7e3629bf93b2f43e553ebd518198c2cc1a782bcc3d37e1304f431c9997c803368f54ef2f2774f42543c32d"
    )


def test_decode_list_not_encrypted():
    client = Client()
    User = get_user_model()
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
    user = User.objects.get(username="decode_list_test")
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
    User.objects.all().delete()
    Signal.objects.all().delete()
    UserKeys.objects.all().delete()


def test_decode_list_encrypted():
    client = Client()
    User = get_user_model()
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
    user = User.objects.get(username="decode_list_test")
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
    User.objects.all().delete()
    Signal.objects.all().delete()
    UserKeys.objects.all().delete()


def test_decode_long_signal_list():
    client = Client()
    User = get_user_model()
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
    user = User.objects.get(username="decode_long_list_test")
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
    print(len(response.json()))
    assert len(response.json()) == 100
    User.objects.all().delete()
    Signal.objects.all().delete()
    UserKeys.objects.all().delete()


def test_decode_list_does_not_exist():
    client = Client()
    User = get_user_model()
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
    user = User.objects.get(username="decode_list_does_not_exist_test")
    baker.make(UserKeys, user=user)
    response = client.post(
        "/v1/whiteflag/decode_list/",
        {"signals": [0]},
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json() == []
    User.objects.all().delete()
    Signal.objects.all().delete()
    UserKeys.objects.all().delete()
