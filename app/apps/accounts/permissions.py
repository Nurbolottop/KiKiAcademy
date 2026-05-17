from functools import wraps

from django.shortcuts import redirect
from django.urls import reverse

from apps.lms.models import Role


def is_founder(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    if not profile:
        return False
    return profile.roles.filter(code=Role.Code.FOUNDER).exists()


def post_login_redirect_url(user) -> str:
    if is_founder(user):
        return reverse('admin_panel:dashboard')
    return reverse('dashboard')


def founder_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        if not is_founder(request.user):
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
