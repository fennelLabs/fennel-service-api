from django.test import Client, TestCase
from django.urls import reverse

from dashboard.models import User


class TestAuthViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.client.post(
            reverse("dashboard:register"),
            {
                "username": "testuser",
                "password": "testpass",
                "password2": "testpass",
                "email": "test@test.com",
                "first_name": "test",
                "last_name": "user",
            },
        )
        self.user = User.objects.get(username="testuser")

    def test_register(self):
        response = self.client.get(reverse("dashboard:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/register.html")

    def test_login(self):
        response = self.client.get(reverse("dashboard:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/login.html")

    def test_login_is_valid(self):
        response = self.client.post(
            reverse("dashboard:login"), {"username": "testuser", "password": "testpass"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("dashboard:index"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=False,
        )
        assert response.wsgi_request.user.is_authenticated

    def test_login_already_authenticated(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("dashboard:login"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("dashboard:index"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=False,
        )

    def test_logout(self):
        self.client.get(reverse("dashboard:logout"))

    def test_change_password(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("dashboard:change_password"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/change_password.html")

    def test_change_password_post(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("dashboard:change_password"),
            {
                "old_password": "testpass",
                "new_password1": "testpass2",
                "new_password2": "testpass2",
            },
        )
        self.assertRedirects(
            response,
            reverse("dashboard:index"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=False,
        )
        assert User.objects.get(username="testuser").check_password("testpass2")

    def test_change_password_post_invalid(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("dashboard:change_password"),
            {
                "old_password": "testpass",
                "new_password1": "testpass2",
                "new_password2": "testpass3",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/change_password.html")
        assert User.objects.get(username="testuser").check_password("testpass")
