from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Client


class ClientCreateTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="password")
        self.client.force_login(self.user)

    def test_client_create_view(self):
        response = self.client.post(
            reverse("clients:create"),
            {
                "name": "New Client",
                "platform": "Direct",
                "email": "new@example.com",
                "company": "Example Co",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Client.objects.filter(name="New Client").exists())

    def test_client_health_view(self):
        Client.objects.create(name="Health Client", platform="Direct")
        response = self.client.get(reverse("clients:health"))
        self.assertEqual(response.status_code, 200)
