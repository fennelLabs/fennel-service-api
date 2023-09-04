from django.test import TestCase
from django.test.client import Client


class TestAPIViews(TestCase):
    def test_healthcheck(self):
        client = Client()
        response = client.get("/v1/healthcheck/")
        assert response.status_code == 200

    def test_get_version(self):
        client = Client()
        response = client.get("/v1/get_version/")
        assert response.status_code == 200
        assert response.json()["version"] is not None
