import pytest
from rest_framework.test import APIClient
from django.urls import reverse

@pytest.fixture
def api_client():
    return APIClient()

def test_health_endpoint(api_client):
    url = reverse('health')
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data['status'] == 'healthy'

def test_feedback_endpoint(api_client):
    url = reverse('feedback')
    data = {"message_id": "123", "rating": 1, "comment": "Great!"}
    response = api_client.post(url, data, format='json')
    assert response.status_code == 200
    assert response.data['status'] == 'feedback recorded'

def test_chat_missing_message(api_client):
    url = reverse('chat')
    response = api_client.post(url, {}, format='json')
    assert response.status_code == 400
