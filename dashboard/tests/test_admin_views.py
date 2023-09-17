from django.test import Client, TestCase
from django.urls import reverse

from dashboard.models import APIGroup, APIGroupJoinRequest, User


class AdminViewsTests(TestCase):
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
        APIGroup.objects.create(name="testgroup").admin_list.add(
            User.objects.get(username="testuser")
        )

    def test_api_group_members_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse(
                "dashboard:api_group_members",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/member_list.html")

    def test_api_group_join_requests_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse(
                "dashboard:api_group_join_requests",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/request_list.html")

    def test_accept_join_request_view(self):
        self.client.login(username="testuser", password="testpass")
        User.objects.create_user(
            username="testuser2", password="testpass", email="testuser2@test.com"
        )
        join = APIGroupJoinRequest.objects.create(
            api_group=APIGroup.objects.get(name="testgroup"),
            user=User.objects.get(username="testuser2"),
        )
        response = self.client.get(
            reverse(
                "dashboard:accept_join_request",
                kwargs={
                    "group_id": APIGroup.objects.get(name="testgroup").id,
                    "request_id": join.id,
                },
            )
        )
        self.assertRedirects(
            response,
            reverse(
                "dashboard:api_group_join_requests",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            ),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        assert APIGroupJoinRequest.objects.get(id=join.id).accepted is True

    def test_reject_join_request_view(self):
        self.client.login(username="testuser", password="testpass")
        User.objects.create_user(
            username="testuser2", password="testpass", email="testuser2@test.com"
        )
        join = APIGroupJoinRequest.objects.create(
            api_group=APIGroup.objects.get(name="testgroup"),
            user=User.objects.get(username="testuser2"),
        )
        response = self.client.get(
            reverse(
                "dashboard:reject_join_request",
                kwargs={
                    "group_id": APIGroup.objects.get(name="testgroup").id,
                    "request_id": join.id,
                },
            )
        )
        self.assertRedirects(
            response,
            reverse(
                "dashboard:api_group_join_requests",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            ),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        assert APIGroupJoinRequest.objects.get(id=join.id).rejected is True
        assert APIGroupJoinRequest.objects.get(id=join.id).accepted is False

    def test_api_group_members(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse(
                "dashboard:api_group_members",
                kwargs={"group_id": APIGroup.objects.get(name="testgroup").id},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/member_list.html")

    def test_remove_group_member(self):
        self.client.login(username="testuser", password="testpass")
        User.objects.create_user(
            username="testuser2", password="testpass", email="test2@test.com"
        )
        group = APIGroup.objects.get(name="testgroup")
        group.user_list.add(User.objects.get(username="testuser2"))
        response = self.client.get(
            reverse(
                "dashboard:remove_group_member",
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
        group = APIGroup.objects.get(name="testgroup")
        assert User.objects.get(username="testuser2") not in group.user_list.all()
