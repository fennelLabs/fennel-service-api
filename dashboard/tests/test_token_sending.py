import os
import random
from django.test import Client, TestCase
from django.urls import reverse
import requests

from dashboard.models import APIGroup, APIGroupJoinRequest, User, UserKeys


class TestTokenSending(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="test_user", password="test_password"
        )
        UserKeys.objects.create(
            user=self.user,
            mnemonic="bottom drive obey lake curtain smoke basket hold race lonely fit walk//Alice",
            address="5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
        )
        self.group = APIGroup.objects.create(name="test_group")
        self.group.admin_list.add(self.user)
        self.group.user_list.add(self.user)
        self.group.save()
        self.client.login(username="test_user", password="test_password")
        User.objects.create_user(username="new_user", password="new_password")
        for i in range(10):
            User.objects.create_user(
                username=f"new{i}_user", password="new_password"
            )
        shuffled_users = list(User.objects.all())
        random.shuffle(shuffled_users)
        for user in shuffled_users:
            request = APIGroupJoinRequest.objects.create(api_group=self.group, user=user)
            self.client.get(
                reverse("dashboard:api_group_join_requests", args=[self.group.id])
            )
            self.client.post(
                reverse(
                    "dashboard:accept_join_request",
                    args=[self.group.id, request.id],
                )
            )
            self.client.post(
                reverse(
                    "dashboard:create_wallet_for_member",
                    kwargs={
                        "group_id": APIGroup.objects.get(name="test_group").id,
                        "member_id": user.id,
                    },
                ),
            )
        for i in range(10):
            user = User.objects.create_user(
                username=f"test{i}_user", password="test_password"
            )
            UserKeys.objects.create(
                user=user,
            )
            group = APIGroup.objects.create(name=f"test{i}_group")
            group.admin_list.add(user)
            group.user_list.add(user)
            for j in range(10):
                non_admin_user = User.objects.create_user(
                    username=f"test{i}_user_{j}", password="test_password"
                )
                group.user_list.add(non_admin_user)
            group.save()

    def test_transfer_tokens_to_address_send_to_self(self):
        response = self.client.post(
            reverse(
                "dashboard:transfer_tokens_to_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="test_group").id,
                    "member_id": User.objects.get(username="test_user").id,
                },
            ),
            data={"amount": 10},
        )
        self.assertTemplateUsed(response, "dashboard/confirm_transfer_tokens_to_member.html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test_user")

    def test_transfer_tokens_to_address_check_usernames(self):
        response = self.client.post(
            reverse(
                "dashboard:transfer_tokens_to_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="test_group").id,
                    "member_id": User.objects.get(username="new_user").id,
                },
            ),
            data={"amount": 10},
        )
        self.assertTemplateUsed(response, "dashboard/confirm_transfer_tokens_to_member.html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "new_user")


    def test_transfer_tokens_to_address_check_usernames_multiple(self):
        response = self.client.post(
            reverse(
                "dashboard:transfer_tokens_to_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="test_group").id,
                    "member_id": User.objects.get(username="new2_user").id,
                },
            ),
            data={"amount": 10},
        )
        self.assertTemplateUsed(response, "dashboard/confirm_transfer_tokens_to_member.html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Are you sure you want to send 10 tokens to new2_user with a fee of 0.0 ?")
        response = self.client.post(
            reverse(
                "dashboard:transfer_tokens_to_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="test_group").id,
                    "member_id": User.objects.get(username="new3_user").id,
                },
            ),
            data={"amount": 10},
        )
        self.assertTemplateUsed(response, "dashboard/confirm_transfer_tokens_to_member.html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Are you sure you want to send 10 tokens to new3_user with a fee of 0.0 ?")

    def test_transfer_tokens_to_address_post(self):
        response = self.client.post(
            reverse(
                "dashboard:transfer_tokens_to_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="test_group").id,
                    "member_id": User.objects.get(username="new_user").id,
                },
            ),
            data={"amount": 10},
        )
        self.assertTemplateUsed(
            response, "dashboard/confirm_transfer_tokens_to_member.html"
        )

    def test_try_big_multiply(self):
        self.assertEqual(10 * 1000000000000, 10000000000000)

    def test_confirm_transfer_tokens_to_address_post(self):
        self.client.post(
            reverse(
                "dashboard:confirm_transfer_tokens_to_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="test_group").id,
                    "member_id": User.objects.get(username="new_user").id,
                },
            ),
            data={"amount": 10},
        )

    def test_confirm_transfer_tokens_404(self):
        self.client.post(
            path="/api/dashboard/members/1/transfer/1/confirm/",
            data={"amount": 50},
            content_type="application/x-www-form-urlencoded",
        )

    def test_big_multiply_call(self):
        math_response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/big_multiply",
            json={"a": "50", "b": "1000000000000"},
            timeout=5,
        )
        self.assertEqual(math_response.status_code, 200)
        self.assertEqual(int(math_response.json()["result"]), 50000000000000)
