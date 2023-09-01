from django.test import Client
from django.contrib.auth import get_user_model
from main.models import UserKeys


def test_get_fee_for_new_signal_with_whiteflag_signal_production_crash():
    client = Client()
    user_model = get_user_model()
    auth_response = client.post(
        "/v1/auth/register/",
        {
            "username": "get_fee_for_new_signal_test_whiteflag",
            "password": "get_fee_for_new_signal_test_whiteflag",
            "email": "get_fee_for_new_signal_test_whiteflag@test.com",
        },
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user = user_model.objects.get(username="get_fee_for_new_signal_test_whiteflag")
    response = client.post(
        "/v1/fennel/create_account/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert UserKeys.objects.filter(user=user).first().mnemonic is not None
    assert UserKeys.objects.filter(user=user).first().mnemonic != ""
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
    payload = {
        "signal": encode_response.json(),
    }
    response = client.post(
        "/v1/fennel/get_fee_for_new_signal/",
        payload,
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["fee"] is not None
    assert response.json()["fee"] > 0
    user_model.objects.all().delete()
    UserKeys.objects.all().delete()


def test_get_fee_for_new_signal_with_whiteflag_signal_production_crash_2():
    client = Client()
    user_model = get_user_model()
    auth_response = client.post(
        "/v1/auth/register/",
        {
            "username": "get_fee_for_new_signal_test_whiteflag_2",
            "password": "get_fee_for_new_signal_test_whiteflag_2",
            "email": "get_fee_for_new_signal_test_whiteflag_2@test.com",
        },
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user = user_model.objects.get(username="get_fee_for_new_signal_test_whiteflag_2")
    response = client.post(
        "/v1/fennel/create_account/",
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert UserKeys.objects.filter(user=user).first().mnemonic is not None
    assert UserKeys.objects.filter(user=user).first().mnemonic != ""
    payload = {
        "signal": "5746313024a00000000000000000000000000000000000000000000000000000000000000002910118480881290000000114e4245102400706000000000000"
    }
    response = client.post(
        "/v1/fennel/get_fee_for_new_signal/",
        payload,
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    print(response.json())
    assert response.status_code == 200
    assert response.json()["fee"] is not None
    assert response.json()["fee"] > 0
    user_model.objects.all().delete()
    UserKeys.objects.all().delete()
