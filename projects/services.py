from payments.models import Payment


def default_payment_method(project):
    if project.platform == project.Platform.FIVERR:
        return Payment.Method.FIVERR
    if project.platform == project.Platform.UPWORK:
        return Payment.Method.UPWORK
    return Payment.Method.WISE


def settle_completed_project(project, received_date=None):
    if project.status != project.Status.COMPLETED:
        return None
    received_date = received_date or project.delivery_date
    amount = project.hourly_earnings if project.contract_type == project.ContractType.HOURLY and project.hourly_earnings > 0 else project.budget
    payment = project.payments.filter(category=Payment.Category.CONTRACT).order_by("-date_received", "-created_at").first()
    if payment:
        payment.amount = amount
        payment.status = Payment.Status.RECEIVED
        payment.date_received = received_date
        payment.payment_method = payment.payment_method or default_payment_method(project)
        payment.save(update_fields=["amount", "status", "date_received", "payment_method"])
        return payment
    return Payment.objects.create(
        project=project,
        amount=amount,
        category=Payment.Category.CONTRACT,
        payment_method=default_payment_method(project),
        status=Payment.Status.RECEIVED,
        date_received=received_date,
    )
