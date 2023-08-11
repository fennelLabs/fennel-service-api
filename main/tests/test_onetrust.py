from django.test import Client
from django.contrib.auth import get_user_model
from main.models import APIGroup, UserKeys


def test_create_self_custodial_account():
    client = Client()
    User = get_user_model()
    auth_response = client.post(
        "/v1/auth/register/",
        {
            "username": "create_self_custodial_account_test",
            "password": "create_self_custodial_account_test",
            "email": "create_self_custodial_account_test@test.com",
        },
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user = User.objects.get(username="create_self_custodial_account_test")
    response = client.post(
        "/v1/group/create/",
        {"api_group_name": "test", "email": "test@test.com"},
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    response = client.post(
        "/v1/onetrust/create_self_custodial_account/",
        {
            "api_key": response.json()["api_key"],
            "api_secret": response.json()["api_secret"],
        },
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert UserKeys.objects.filter(user=user).first().key_shard is not None
    assert UserKeys.objects.filter(user=user).first().key_shard != ""
    assert response.json()["user_shard"] is not None
    assert response.json()["recovery_shard"] is not None
    User.objects.all().delete()
    UserKeys.objects.all().delete()
    APIGroup.objects.all().delete()


def test_reconstruct_self_custodial_account():
    client = Client()
    User = get_user_model()
    auth_response = client.post(
        "/v1/auth/register/",
        {
            "username": "reconstruct_self_custodial_account_test",
            "password": "reconstruct_self_custodial_account_test",
            "email": "reconstruct_self_custodial_account_test@test.com",
        },
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user = User.objects.get(username="reconstruct_self_custodial_account_test")
    response = client.post(
        "/v1/group/create/",
        {"api_group_name": "test", "email": "test@test.com"},
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["api_key"] is not None
    assert response.json()["api_secret"] is not None
    api_key = response.json()["api_key"]
    api_secret = response.json()["api_secret"]
    response = client.post(
        "/v1/onetrust/create_self_custodial_account/",
        {
            "api_key": api_key,
            "api_secret": api_secret,
        },
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert UserKeys.objects.filter(user=user).first().key_shard is not None
    assert UserKeys.objects.filter(user=user).first().key_shard != ""
    assert response.json()["user_shard"] is not None
    assert response.json()["recovery_shard"] is not None
    assert response.json()["address"] is not None
    assert response.json()["public_key"] is not None
    payload = {
        "user_shard": response.json()["user_shard"],
        "api_key": api_key,
        "api_secret": api_secret,
    }
    response = client.post(
        "/v1/onetrust/reconstruct_self_custodial_account/",
        payload,
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["mnemonic"] is not None
    User.objects.all().delete()
    UserKeys.objects.all().delete()
    APIGroup.objects.all().delete()


def test_get_self_custodial_account_address():
    client = Client()
    User = get_user_model()
    auth_response = client.post(
        "/v1/auth/register/",
        {
            "username": "get_self_custodial_account_address_test",
            "password": "get_self_custodial_account_address_test",
            "email": "get_self_custodial_account_address_test@test.com",
        },
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    user = User.objects.get(username="get_self_custodial_account_address_test")
    response = client.post(
        "/v1/group/create/",
        {"api_group_name": "test", "email": "test_group@test.com"},
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["api_key"] is not None
    assert response.json()["api_secret"] is not None
    api_key = response.json()["api_key"]
    api_secret = response.json()["api_secret"]
    response = client.post(
        "/v1/onetrust/create_self_custodial_account/",
        {
            "api_key": api_key,
            "api_secret": api_secret,
        },
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert UserKeys.objects.filter(user=user).first().key_shard is not None
    assert UserKeys.objects.filter(user=user).first().key_shard != ""
    assert response.json()["user_shard"] is not None
    assert response.json()["recovery_shard"] is not None
    assert response.json()["address"] is not None
    address = response.json()["address"]
    assert response.json()["public_key"] is not None
    payload = {
        "user_shard": response.json()["user_shard"],
        "api_key": api_key,
        "api_secret": api_secret,
    }
    response = client.post(
        "/v1/onetrust/reconstruct_self_custodial_account/",
        payload,
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["mnemonic"] is not None
    payload = {
        "mnemonic": response.json()["mnemonic"],
        "api_key": api_key,
        "api_secret": api_secret,
    }
    response = client.post(
        "/v1/onetrust/get_self_custodial_account_address/",
        payload,
        HTTP_AUTHORIZATION=f'Token {auth_response.json()["token"]}',
    )
    assert response.status_code == 200
    assert response.json()["address"] is not None
    assert response.json()["address"] == address
    User.objects.all().delete()
    UserKeys.objects.all().delete()
    APIGroup.objects.all().delete()
