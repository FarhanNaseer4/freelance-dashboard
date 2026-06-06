from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from clients.models import Client
from payments.models import Payment
from projects.models import Activity, Milestone, Project, ProjectNote, Tag, TimeLog


class Command(BaseCommand):
    help = "Seed realistic demo data for the freelance dashboard."

    def handle(self, *args, **options):
        today = timezone.localdate()
        tags = {
            "urgent": Tag.objects.get_or_create(name="urgent", defaults={"color": "#ef4444"})[0],
            "automation": Tag.objects.get_or_create(name="automation", defaults={"color": "#0ea5e9"})[0],
            "dashboard": Tag.objects.get_or_create(name="dashboard", defaults={"color": "#22c55e"})[0],
            "scraping": Tag.objects.get_or_create(name="scraping", defaults={"color": "#a855f7"})[0],
        }

        clients = {}
        for name, platform, email, company in [
            ("Lindsey", Client.Platform.FIVERR, "lindsey@example.com", ""),
            ("Lauren", Client.Platform.UPWORK, "lauren@example.com", "Studio North"),
            ("Brandon", Client.Platform.UPWORK, "brandon@example.com", "Brandon Analytics"),
            ("Ayo Peter", Client.Platform.DIRECT, "ayo@example.com", "Ayo Labs"),
            ("Ben Webb", Client.Platform.DIRECT, "ben@example.com", "Webb Research"),
            ("Miodrag", Client.Platform.FIVERR, "miodrag@example.com", ""),
            ("Boris Z", Client.Platform.UPWORK, "boris@example.com", "BZ Ops"),
        ]:
            clients[name], _ = Client.objects.update_or_create(
                name=name,
                defaults={
                    "platform": platform,
                    "email": email,
                    "company": company,
                    "notes": "Demo client seeded for the freelance management dashboard.",
                    "first_contact_date": today - timedelta(days=60),
                    "last_contact_date": today - timedelta(days=2),
                },
            )

        lindsey = self.project(
            clients["Lindsey"],
            "Single-page delivery tracker",
            Project.Platform.FIVERR,
            Project.ContractType.FIXED,
            Project.ProjectType.DASHBOARD,
            Decimal("40"),
            today - timedelta(days=8),
            today - timedelta(days=1),
            Project.Status.COMPLETED,
            Project.Priority.LOW,
            "Delivered final dashboard and handoff notes.",
        )
        lindsey.tags.add(tags["dashboard"])
        Payment.objects.update_or_create(project=lindsey, amount=Decimal("40"), defaults={"date_received": today - timedelta(days=1), "payment_method": Payment.Method.FIVERR, "status": Payment.Status.RECEIVED})

        ben = self.project(
            clients["Ben Webb"],
            "Research data extraction pipeline",
            Project.Platform.DIRECT,
            Project.ContractType.MILESTONE,
            Project.ProjectType.DATA_EXTRACTION,
            Decimal("400"),
            today - timedelta(days=10),
            today + timedelta(days=12),
            Project.Status.WORKING,
            Project.Priority.HIGH,
            "Build extraction workflow and delivery-ready dataset.",
            "Share milestone 2 preview",
            today + timedelta(days=2),
        )
        ben.tags.add(tags["scraping"], tags["urgent"])
        for title, amount, offset, status, payment_status in [
            ("Milestone 1 - source mapping", Decimal("100"), -3, Milestone.Status.COMPLETED, Milestone.PaymentStatus.RECEIVED),
            ("Milestone 2 - extraction build", Decimal("150"), 4, Milestone.Status.IN_PROGRESS, Milestone.PaymentStatus.PENDING),
            ("Milestone 3 - QA and final delivery", Decimal("150"), 12, Milestone.Status.PENDING, Milestone.PaymentStatus.PENDING),
        ]:
            Milestone.objects.update_or_create(
                project=ben,
                title=title,
                defaults={"amount": amount, "due_date": today + timedelta(days=offset), "status": status, "payment_status": payment_status, "delivery_notes": "Tracked in demo milestone plan."},
            )
        Payment.objects.update_or_create(project=ben, amount=Decimal("100"), defaults={"date_received": today - timedelta(days=3), "payment_method": Payment.Method.WISE, "status": Payment.Status.RECEIVED})
        Payment.objects.update_or_create(project=ben, amount=Decimal("150"), defaults={"payment_method": Payment.Method.WISE, "status": Payment.Status.PENDING})

        brandon = self.project(
            clients["Brandon"],
            "Hourly Django automation support",
            Project.Platform.UPWORK,
            Project.ContractType.HOURLY,
            Project.ProjectType.DJANGO,
            Decimal("1125"),
            today - timedelta(days=20),
            today + timedelta(days=8),
            Project.Status.RUNNING,
            Project.Priority.MEDIUM,
            "Ongoing hourly support for internal automation.",
            "Send weekly update",
            today + timedelta(days=1),
            hourly_rate=Decimal("75"),
            expected_hours=Decimal("20"),
            billed_hours=Decimal("12"),
        )
        brandon.tags.add(tags["automation"])
        for days, hours, desc in [(-5, Decimal("4.0"), "Workflow cleanup"), (-3, Decimal("3.5"), "Bug fixes"), (-1, Decimal("2.5"), "Deployment support")]:
            TimeLog.objects.update_or_create(project=brandon, date=today + timedelta(days=days), defaults={"hours": hours, "description": desc})
        Payment.objects.update_or_create(project=brandon, amount=Decimal("750"), defaults={"date_received": today - timedelta(days=2), "payment_method": Payment.Method.UPWORK, "status": Payment.Status.RECEIVED})

        examples = [
            ("Lauren", "Power BI sales visibility dashboard", Project.Platform.UPWORK, Project.ContractType.FIXED, Project.ProjectType.POWER_BI, "650", 18, Project.Status.WAITING_CLIENT, Project.Priority.MEDIUM),
            ("Ayo Peter", "Lead generation automation", Project.Platform.DIRECT, Project.ContractType.FIXED, Project.ProjectType.LEAD_GENERATION, "300", 3, Project.Status.WAITING_CREDENTIALS, Project.Priority.HIGH),
            ("Miodrag", "Fiverr scraping order pack", Project.Platform.FIVERR, Project.ContractType.FIXED, Project.ProjectType.WEB_SCRAPING, "120", -2, Project.Status.DELIVERED, Project.Priority.MEDIUM),
            ("Boris Z", "Operations analytics mini CRM", Project.Platform.UPWORK, Project.ContractType.MILESTONE, Project.ProjectType.DASHBOARD, "900", 25, Project.Status.ON_HOLD, Project.Priority.LOW),
        ]
        for client_name, title, platform, contract, project_type, budget, due_offset, status, priority in examples:
            project = self.project(clients[client_name], title, platform, contract, project_type, Decimal(budget), today - timedelta(days=14), today + timedelta(days=due_offset), status, priority, "Seeded realistic project example.", "Confirm next step", today + timedelta(days=max(due_offset, 1)))
            project.tags.add(tags["dashboard"] if project_type in [Project.ProjectType.DASHBOARD, Project.ProjectType.POWER_BI] else tags["automation"])
            if status in [Project.Status.DELIVERED, Project.Status.COMPLETED]:
                Payment.objects.update_or_create(project=project, amount=Decimal(budget), defaults={"date_received": today - timedelta(days=1), "payment_method": Payment.Method.FIVERR if platform == Project.Platform.FIVERR else Payment.Method.UPWORK, "status": Payment.Status.RECEIVED})
            else:
                Payment.objects.update_or_create(project=project, amount=Decimal(budget) / 2, defaults={"payment_method": Payment.Method.PAYPAL, "status": Payment.Status.PENDING})

        for project in Project.objects.all():
            ProjectNote.objects.get_or_create(project=project, body="Demo note: keep communication concise and document delivery decisions.")
            Activity.objects.get_or_create(project=project, action="Seeded", defaults={"description": "Created by seed_demo_data."})

        self.stdout.write(self.style.SUCCESS("Seeded freelance dashboard demo data."))

    def project(self, client, name, platform, contract_type, project_type, budget, start, delivery, status, priority, description, next_action="", follow_up=None, hourly_rate=None, expected_hours=None, billed_hours=None):
        project, _ = Project.objects.update_or_create(
            client=client,
            name=name,
            defaults={
                "platform": platform,
                "contract_type": contract_type,
                "project_type": project_type,
                "budget": budget,
                "start_date": start,
                "delivery_date": delivery,
                "status": status,
                "priority": priority,
                "description": description,
                "notes": "Seeded demo project.",
                "next_action": next_action,
                "follow_up_date": follow_up,
                "hourly_rate": hourly_rate,
                "expected_hours": expected_hours,
                "billed_hours": billed_hours,
            },
        )
        return project
