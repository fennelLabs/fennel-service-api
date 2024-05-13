from django.test import Client, TestCase
from django.urls import reverse

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
        new_user = User.objects.create_user(
            username="new_user", password="new_password"
        )
        APIGroupJoinRequest.objects.create(api_group=self.group, user=new_user)
        self.client.get(
            reverse("dashboard:api_group_join_requests", args=[self.group.id])
        )
        self.client.post(
            reverse(
                "dashboard:accept_join_request",
                args=[self.group.id, APIGroupJoinRequest.objects.first().id],
            )
        )
        self.client.post(
            reverse(
                "dashboard:create_wallet_for_member",
                kwargs={
                    "group_id": APIGroup.objects.get(name="test_group").id,
                    "member_id": User.objects.get(username="new_user").id,
                },
            ),
        )

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
