from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from clients.models import Client
from core.analytics import dashboard_metrics, revenue_by_client, revenue_by_month, revenue_by_platform
from payments.models import Payment
from projects.models import Project


class DashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="password")
        self.client.force_login(self.user)
        client = Client.objects.create(name="Lindsey", platform=Client.Platform.FIVERR)
        project = Project.objects.create(
            client=client,
            name="Fixed project",
            platform=Project.Platform.FIVERR,
            contract_type=Project.ContractType.FIXED,
            project_type=Project.ProjectType.DASHBOARD,
            budget=Decimal("40"),
            status=Project.Status.COMPLETED,
        )
        Payment.objects.create(project=project, amount=Decimal("40"), payment_method=Payment.Method.FIVERR, status=Payment.Status.RECEIVED, date_received="2026-06-01")

    def test_dashboard_metrics(self):
        metrics = dashboard_metrics()
        self.assertEqual(metrics["total_revenue"], Decimal("40"))
        self.assertEqual(metrics["completed_projects"], 1)

    def test_platform_fee_net_revenue_metrics(self):
        client = Client.objects.create(name="Upwork Client", platform=Client.Platform.UPWORK)
        project = Project.objects.create(
            client=client,
            name="Upwork project",
            platform=Project.Platform.UPWORK,
            contract_type=Project.ContractType.FIXED,
            project_type=Project.ProjectType.AUTOMATION,
            budget=Decimal("100"),
        )
        Payment.objects.create(project=project, amount=Decimal("100"), payment_method=Payment.Method.UPWORK, status=Payment.Status.RECEIVED, date_received="2026-06-06")
        metrics = dashboard_metrics()
        self.assertEqual(metrics["platform_fees_this_month"], Decimal("18.00"))
        self.assertEqual(metrics["net_revenue_this_month"], Decimal("122.00"))

    def test_revenue_groupings(self):
        self.assertEqual(revenue_by_platform()[0]["label"], "Fiverr")
        self.assertEqual(revenue_by_client()[0]["label"], "Lindsey")
        self.assertTrue(revenue_by_month())

    def test_pages_render(self):
        for name in ["dashboard:home", "dashboard:analytics", "dashboard:calendar", "dashboard:followups"]:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
