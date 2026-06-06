from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from clients.models import Client
from projects.management.commands.seed_demo_data import Command
from projects.models import Project
from .services import validate_and_import


class ImportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="password")
        self.client.force_login(self.user)

    def test_project_import_validation(self):
        results = validate_and_import([
            {"client": "Ayo Peter", "project": "Automation", "platform": "Direct", "contract_type": "Fixed Price", "project_type": "Automation", "budget": "300"}
        ], commit=True)
        self.assertTrue(results[0]["valid"])
        self.assertTrue(Client.objects.filter(name="Ayo Peter").exists())
        self.assertTrue(Project.objects.filter(name="Automation").exists())

    def test_import_page_accepts_csv(self):
        upload = SimpleUploadedFile("clients.csv", b"name,platform,email\nLindsey,Fiverr,l@example.com\n", content_type="text/csv")
        response = self.client.post(reverse("imports:home"), {"file": upload})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Valid")

    def test_seed_command(self):
        Command().handle()
        self.assertTrue(Client.objects.filter(name="Ben Webb").exists())
        self.assertTrue(Project.objects.filter(contract_type=Project.ContractType.HOURLY).exists())
