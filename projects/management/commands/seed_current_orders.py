from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand

from clients.models import Client
from payments.models import Payment
from projects.models import Activity, Milestone, Project, ProjectNote


class Command(BaseCommand):
    help = "Load the current real orders from the provided tracking sheet."

    rows = [
        ("Fiverr", "Lindsey", "06/01/2026", "40", 1, 1, "40", "Running", "Need to give client 10k records"),
        ("Fiverr", "Lauren", "06/01/2026", "40", 1, 1, "40", "Running", "Need to give client 10k records"),
        ("Upwork", "Brandon", "06/02/2024", "40", 1, 1, "40", "Completed", "2 hours logged"),
        ("Upwork", "Ayo Peter", "06/03/2026", "150", 1, 1, "150", "Data Shared", "Waiting for client Response"),
        ("Upwork", "Ben Webb", "06/03/2026", "400", 3, 1, "100", "Working", "Rental and sale script completed"),
        ("Upwork", "Miodrag", "06/01/2026", "150", 1, 1, "150", "Working", "Waiting for DB credentials"),
        ("Upwork", "Boris Z", "05/22/2026", "200", 2, 2, "100", "Running", "Cenotako script running"),
    ]

    def handle(self, *args, **options):
        for platform, client_name, placed_on, budget, total_milestones, current_milestone, current_cost, status, note in self.rows:
            start_date = datetime.strptime(placed_on, "%m/%d/%Y").date()
            client, _ = Client.objects.update_or_create(
                name=client_name,
                defaults={
                    "platform": platform,
                    "last_contact_date": start_date,
                    "first_contact_date": start_date,
                    "notes": note,
                },
            )
            project, _ = Project.objects.update_or_create(
                client=client,
                name=f"{client_name} Order",
                defaults={
                    "platform": platform,
                    "contract_type": Project.ContractType.MILESTONE if total_milestones > 1 else Project.ContractType.FIXED,
                    "project_type": Project.ProjectType.DATA_EXTRACTION,
                    "start_date": start_date,
                    "delivery_date": None,
                    "budget": Decimal(budget),
                    "status": status,
                    "priority": Project.Priority.MEDIUM if status != Project.Status.WORKING else Project.Priority.HIGH,
                    "description": note,
                    "notes": note,
                    "next_action": note,
                },
            )
            project.milestones.all().delete()
            for index in range(1, total_milestones + 1):
                if index < current_milestone or status == Project.Status.COMPLETED:
                    milestone_status = Milestone.Status.COMPLETED
                    payment_status = Milestone.PaymentStatus.RECEIVED
                elif index == current_milestone:
                    milestone_status = Milestone.Status.IN_PROGRESS if status not in [Project.Status.COMPLETED, Project.Status.DATA_SHARED] else Milestone.Status.COMPLETED
                    payment_status = Milestone.PaymentStatus.PENDING
                else:
                    milestone_status = Milestone.Status.PENDING
                    payment_status = Milestone.PaymentStatus.PENDING
                amount = Decimal(current_cost) if index == current_milestone else Decimal(budget) / Decimal(total_milestones)
                Milestone.objects.create(
                    project=project,
                    title=f"Milestone {index}",
                    amount=amount,
                    status=milestone_status,
                    payment_status=payment_status,
                    delivery_notes=note if index == current_milestone else "",
                )
            Payment.objects.filter(project=project).delete()
            if status == Project.Status.COMPLETED:
                Payment.objects.create(project=project, amount=Decimal(budget), payment_method=Payment.Method.UPWORK if platform == "Upwork" else Payment.Method.FIVERR, status=Payment.Status.RECEIVED, date_received=start_date)
            ProjectNote.objects.update_or_create(project=project, body=note)
            Activity.objects.update_or_create(project=project, action="Imported", defaults={"description": "Loaded from current order sheet."})
        self.stdout.write(self.style.SUCCESS("Loaded current real orders."))
