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
