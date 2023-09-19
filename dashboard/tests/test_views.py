from django.test import Client, TestCase
from django.urls import reverse

from dashboard.models import APIGroup, APIGroupJoinRequest, User


class ViewsTests(TestCase):
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

    def test_dashboard_view(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertRedirects(
            response,
            reverse("dashboard:login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_dashboard_view_logged_in(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/index.html")

    def test_dashboard_view_logged_in_with_api_group(self):
        self.client.login(username="testuser", password="testpass")
        APIGroup.objects.create(name="testgroup").admin_list.add(
            User.objects.get(username="testuser")
        )
        response = self.client.get(reverse("dashboard:index"))
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

    def test_create_api_group_view(self):
        response = self.client.get(reverse("dashboard:create_api_group"))
        self.assertRedirects(
            response,
            reverse("dashboard:login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_create_api_group_view_post(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("dashboard:create_api_group"), {"group_name": "testgroup"}
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
        self.assertEqual(APIGroup.objects.count(), 1)
        self.assertEqual(APIGroup.objects.first().name, "testgroup")
        self.assertEqual(
            APIGroup.objects.first().admin_list.first().username, "testuser"
        )

    def test_create_api_group_view_post_reused_name(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("dashboard:create_api_group"), {"group_name": "testgroup"}
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
        self.assertEqual(APIGroup.objects.count(), 1)
        self.assertEqual(APIGroup.objects.first().name, "testgroup")
        self.assertEqual(
            APIGroup.objects.first().admin_list.first().username, "testuser"
        )
        response = self.client.post(
            reverse("dashboard:create_api_group"), {"group_name": "testgroup"}
        )
        self.assertEqual(APIGroup.objects.count(), 1)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/index.html")

    def test_get_balance(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("dashboard:get_balance"))
        self.assertRedirects(
            response,
            reverse("dashboard:index"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_get_send_join_request(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("dashboard:send_group_join_request"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/index.html")

    def test_post_send_join_request(self):
        self.client.login(username="testuser", password="testpass")
        APIGroup.objects.create(name="testgroup")
        response = self.client.post(
            reverse("dashboard:send_group_join_request"), {"group_name": "testgroup"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("dashboard:index"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        self.assertEqual(APIGroup.objects.count(), 1)
        self.assertEqual(APIGroup.objects.first().name, "testgroup")
        self.assertEqual(APIGroupJoinRequest.objects.count(), 1)
        self.assertEqual(
            APIGroupJoinRequest.objects.first().api_group.name, "testgroup"
        )
        self.assertEqual(APIGroupJoinRequest.objects.first().user.username, "testuser")

    def test_post_send_join_request_nonexistent_group(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("dashboard:send_group_join_request"), {"group_name": "testgroup"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/index.html")
