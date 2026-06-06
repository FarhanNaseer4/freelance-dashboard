from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin


class DashboardLoginRequiredMixin(LoginRequiredMixin):
    login_url = settings.LOGIN_URL


def dashboard_login_required(view_func):
    return login_required(view_func, login_url=settings.LOGIN_URL)
