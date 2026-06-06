from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from clients.models import Client
from payments.models import Payment
from .models import Milestone, Project, TimeLog


class ProjectCalculationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="password")
        self.client.force_login(self.user)
        self.client_obj = Client.objects.create(name="Client", platform=Client.Platform.DIRECT)
        self.project = Project.objects.create(
            client=self.client_obj,
            name="Milestone project",
            platform=Project.Platform.DIRECT,
            contract_type=Project.ContractType.MILESTONE,
            project_type=Project.ProjectType.DJANGO,
            budget=Decimal("300"),
            delivery_date=timezone.localdate() + timedelta(days=2),
            hourly_rate=Decimal("50"),
        )

    def test_payment_calculations(self):
        Payment.objects.create(project=self.project, amount=Decimal("100"), payment_method=Payment.Method.WISE, status=Payment.Status.RECEIVED, date_received=timezone.localdate())
        Payment.objects.create(project=self.project, amount=Decimal("50"), payment_method=Payment.Method.WISE, status=Payment.Status.PENDING)
        self.assertEqual(self.project.received_amount, Decimal("100"))
        self.assertEqual(self.project.pending_amount, Decimal("50"))
        self.assertEqual(self.project.remaining_amount, Decimal("200"))
        self.assertTrue(self.project.has_pending_payment)

    def test_hourly_calculations(self):
        TimeLog.objects.create(project=self.project, date=timezone.localdate(), hours=Decimal("2.5"))
        TimeLog.objects.create(project=self.project, date=timezone.localdate(), hours=Decimal("1.5"))
        self.assertEqual(self.project.hours_logged, Decimal("4"))
        self.assertEqual(self.project.hourly_earnings, Decimal("200"))

    def test_milestone_progress_and_dates(self):
        Milestone.objects.create(project=self.project, title="One", amount=100, status=Milestone.Status.COMPLETED)
        Milestone.objects.create(project=self.project, title="Two", amount=200, status=Milestone.Status.PENDING)
        self.assertEqual(self.project.progress_percent, 50)
        self.assertTrue(self.project.is_due_soon)
        self.assertFalse(self.project.is_overdue)

    def test_project_list_search_renders(self):
        response = self.client.get(reverse("projects:list"), {"q": "Milestone"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Milestone project")

    def test_completed_projects_are_archived_from_active_table(self):
        completed = Project.objects.create(
            client=self.client_obj,
            name="Completed archive project",
            platform=Project.Platform.DIRECT,
            contract_type=Project.ContractType.FIXED,
            project_type=Project.ProjectType.AUTOMATION,
            budget=Decimal("90"),
            status=Project.Status.COMPLETED,
        )
        active_response = self.client.get(reverse("projects:list"))
        self.assertEqual(active_response.status_code, 200)
        self.assertNotContains(active_response, completed.name)

        completed_response = self.client.get(reverse("projects:completed"))
        self.assertEqual(completed_response.status_code, 200)
        self.assertContains(completed_response, completed.name)

    def test_pipeline_view_renders_active_columns(self):
        response = self.client.get(reverse("projects:pipeline"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Project Pipeline")
        self.assertContains(response, self.project.name)

    def test_project_create_view(self):
        response = self.client.post(
            reverse("projects:create"),
            {
                "client": self.client_obj.pk,
                "name": "New direct project",
                "platform": "Direct",
                "contract_type": "Fixed Price",
                "project_type": "Automation",
                "budget": "120",
                "status": "Running",
                "priority": "Medium",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(name="New direct project").exists())

    def test_exports(self):
        self.assertEqual(self.client.get(reverse("projects:export_csv")).status_code, 200)
        self.assertEqual(self.client.get(reverse("projects:export_excel")).status_code, 200)

    def test_project_detail_actions(self):
        response = self.client.post(
            reverse("projects:add_time_log", kwargs={"pk": self.project.pk}),
            {"date": timezone.localdate(), "hours": "3.0", "description": "Hourly work"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.time_logs.count(), 1)

        response = self.client.post(
            reverse("projects:add_payment", kwargs={"pk": self.project.pk}),
            {"amount": "75", "category": "Contract Payment", "date_received": timezone.localdate(), "payment_method": "Wise", "status": "Received"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.payments.count(), 1)

        response = self.client.post(
            reverse("projects:add_milestone", kwargs={"pk": self.project.pk}),
            {"title": "Three", "amount": "50", "status": "Pending", "payment_status": "Pending", "delivery_notes": "Next"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.project.milestones.filter(title="Three").exists())

    def test_milestone_complete_and_paid_actions(self):
        milestone = Milestone.objects.create(project=self.project, title="Billable", amount=Decimal("80"))
        self.client.post(reverse("projects:mark_milestone_complete", kwargs={"pk": self.project.pk, "milestone_id": milestone.pk}))
        milestone.refresh_from_db()
        self.assertEqual(milestone.status, Milestone.Status.COMPLETED)

        self.client.post(reverse("projects:mark_milestone_paid", kwargs={"pk": self.project.pk, "milestone_id": milestone.pk}))
        milestone.refresh_from_db()
        self.assertEqual(milestone.payment_status, Milestone.PaymentStatus.RECEIVED)
        self.assertTrue(self.project.payments.filter(amount=Decimal("80")).exists())

    def test_quick_status_action(self):
        self.project.delivery_date = timezone.localdate()
        self.project.save(update_fields=["delivery_date"])
        response = self.client.post(reverse("projects:quick_status", kwargs={"pk": self.project.pk, "status": "Completed"}))
        self.assertEqual(response.status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.COMPLETED)
        payment = self.project.payments.get(category=Payment.Category.CONTRACT)
        self.assertEqual(payment.amount, self.project.budget)
        self.assertEqual(payment.date_received, timezone.localdate())

    def test_completed_edit_resettles_existing_payment_date(self):
        payment = Payment.objects.create(
            project=self.project,
            amount=Decimal("300"),
            category=Payment.Category.CONTRACT,
            payment_method=Payment.Method.WISE,
            status=Payment.Status.RECEIVED,
            date_received=timezone.localdate() - timedelta(days=60),
        )
        response = self.client.post(
            reverse("projects:edit", kwargs={"pk": self.project.pk}),
            {
                "client": self.client_obj.pk,
                "name": self.project.name,
                "platform": self.project.platform,
                "contract_type": self.project.contract_type,
                "project_type": self.project.project_type,
                "delivery_date": timezone.localdate(),
                "budget": "300",
                "status": "Completed",
                "priority": "Medium",
            },
        )
        self.assertEqual(response.status_code, 302)
        payment.refresh_from_db()
        self.assertEqual(payment.date_received, timezone.localdate())

    def test_inline_payment_edit_view(self):
        payment = Payment.objects.create(
            project=self.project,
            amount=Decimal("50"),
            category=Payment.Category.CONTRACT,
            payment_method=Payment.Method.WISE,
            status=Payment.Status.PENDING,
        )
        response = self.client.post(
            reverse("projects:edit_payment", kwargs={"pk": self.project.pk, "payment_id": payment.pk}),
            {"amount": "60", "category": "Bonus", "date_received": timezone.localdate(), "payment_method": "Wise", "status": "Received"},
        )
        self.assertEqual(response.status_code, 302)
        payment.refresh_from_db()
        self.assertEqual(payment.amount, Decimal("60.00"))
        self.assertEqual(payment.category, Payment.Category.BONUS)

    def test_tip_bonus_do_not_reduce_remaining_balance(self):
        Payment.objects.create(
            project=self.project,
            amount=Decimal("25"),
            category=Payment.Category.TIP,
            payment_method=Payment.Method.FIVERR,
            status=Payment.Status.RECEIVED,
            date_received=timezone.localdate(),
        )
        Payment.objects.create(
            project=self.project,
            amount=Decimal("50"),
            category=Payment.Category.CONTRACT,
            payment_method=Payment.Method.WISE,
            status=Payment.Status.RECEIVED,
            date_received=timezone.localdate(),
        )
        self.assertEqual(self.project.received_amount, Decimal("75"))
        self.assertEqual(self.project.extra_earnings_amount, Decimal("25"))
        self.assertEqual(self.project.remaining_amount, Decimal("250"))
