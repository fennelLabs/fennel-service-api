from django.test.client import Client
from django.contrib.auth import get_user_model


def test_register_view():
    client = Client()
    response = client.post(
        "/v1/auth/register/",
        {"username": "testuser", "email": "test@test.com", "password": "testpassword"},
    )
    User = get_user_model()
    User.objects.get(username="testuser").delete()
    assert response.status_code == 200


def test_login_view():
    client = Client()
    response = client.post(
        "/v1/auth/register/",
        {"username": "testuser", "email": "test@test.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    response = client.post(
        "/v1/auth/login/", {"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert response.data["token"] is not None
    User = get_user_model()
    User.objects.get(username="testuser").delete()


def test_change_password_view():
    client = Client()
    response = client.post(
        "/v1/auth/register/",
        {
            "username": "test_change_password_user",
            "email": "test_change_password@test.com",
            "password": "testpassword",
        },
    )
    assert response.status_code == 200
    auth_response = client.post(
        "/v1/auth/login/",
        {"username": "test_change_password_user", "password": "testpassword"},
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["token"] is not None
    response = client.post(
        "/v1/auth/change_password/",
        {"old_password": "testpassword", "new_password": "newtestpassword"},
        HTTP_AUTHORIZATION=f'Token {response.json()["token"]}',
    )
    print(response.json())
    assert response.status_code == 200
    response = client.post(
        "/v1/auth/login/",
        {"username": "test_change_password_user", "password": "newtestpassword"},
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None
    User = get_user_model()
    User.objects.all().delete()
