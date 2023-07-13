from django.test.client import Client


def test_healthcheck():
    client = Client()
    response = client.get('/v1/healthcheck/')
    assert response.status_code == 200


def test_get_version():
    client = Client()
    response = client.get('/v1/get_version/')
    assert response.status_code == 200
    assert response.json()['version'] is not None
