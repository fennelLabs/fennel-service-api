from django.test import TestCase, Client
from django.urls import reverse

from dashboard.models import APIGroup, User, UserKeys


class TestWalletViews(TestCase):
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
        self.client.post(
            reverse("dashboard:register"),
            {
                "username": "testuser2",
                "password": "testpass",
                "password2": "testpass",
                "email": "test2@test.com",
                "first_name": "test",
                "last_name": "user2",
            },
        )
        APIGroup.objects.create(name="testgroup").admin_list.add(
            User.objects.get(username="testuser")
        )
        APIGroup.objects.get(name="testgroup").user_list.add(
            User.objects.get(username="testuser2")
        )

    def test_create_wallet(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse(
                "dashboard:create_wallet",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            )
        )
        self.assertRedirects(
            response,
            reverse(
                "dashboard:api_group_members",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            ),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        assert UserKeys.objects.filter(
            user=User.objects.get(username="testuser")
        ).exists()
        assert (
            UserKeys.objects.get(user=User.objects.get(username="testuser")).mnemonic
            is not None
        )

    def test_create_wallet_for_member(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse(
                "dashboard:create_wallet_for_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="testgroup").id,
                    "member_id": User.objects.get(username="testuser2").id,
                },
            )
        )
        self.assertRedirects(
            response,
            reverse(
                "dashboard:api_group_members",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            ),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        assert UserKeys.objects.filter(
            user=User.objects.get(username="testuser2")
        ).exists()
        assert (
            UserKeys.objects.get(user=User.objects.get(username="testuser2")).mnemonic
            is not None
        )
