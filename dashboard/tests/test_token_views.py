from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.messages import get_messages

from dashboard.models import APIGroup, User


class TestTokenViews(TestCase):
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

    def test_transfer_tokens_to_member(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse(
                "dashboard:create_wallet",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            ),
        )
        response = self.client.post(
            reverse(
                "dashboard:create_wallet_for_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="testgroup").id,
                    "member_id": User.objects.get(username="testuser2").id,
                },
            ),
        )
        response = self.client.get(
            reverse(
                "dashboard:transfer_tokens_to_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="testgroup").id,
                    "member_id": User.objects.get(username="testuser2").id,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/transfer_tokens.html")

    def test_transfer_tokens_to_member_no_balance(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse(
                "dashboard:create_wallet",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            ),
        )
        response = self.client.post(
            reverse(
                "dashboard:create_wallet_for_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="testgroup").id,
                    "member_id": User.objects.get(username="testuser2").id,
                },
            ),
        )
        response = self.client.post(
            reverse(
                "dashboard:transfer_tokens_to_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="testgroup").id,
                    "member_id": User.objects.get(username="testuser2").id,
                },
            ),
            {"amount": 10},
        )
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 3)
        self.assertEqual(
            str(messages[-1]),
            "You do not have enough tokens to complete this transaction.",
        )

    def test_get_balance_for_member(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse(
                "dashboard:create_wallet",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            ),
        )
        response = self.client.post(
            reverse(
                "dashboard:create_wallet_for_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="testgroup").id,
                    "member_id": User.objects.get(username="testuser2").id,
                },
            ),
        )
        response = self.client.get(
            reverse(
                "dashboard:get_balance_for_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="testgroup").id,
                    "member_id": User.objects.get(username="testuser2").id,
                },
            ),
        )
        self.assertRedirects(
            response,
            reverse(
                "dashboard:api_group_members",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            ),
        )

    def test_transfer_tokens_to_address(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse(
                "dashboard:create_wallet",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            ),
        )
        response = self.client.post(
            reverse(
                "dashboard:create_wallet_for_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="testgroup").id,
                    "member_id": User.objects.get(username="testuser2").id,
                },
            ),
        )
        response = self.client.get(
            reverse(
                "dashboard:transfer_tokens_to_address",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/transfer_tokens_address.html")
        self.assertContains(response, "form")
        self.assertContains(response, "recipient")
        self.assertContains(response, "amount")
