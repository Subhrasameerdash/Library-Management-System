from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from .models import User


def user_has_role(user: User, roles: Iterable[str]) -> bool:
    return user.is_authenticated and (user.role in roles or user.is_superuser)


class RoleRequiredMixin(LoginRequiredMixin):
    """Mixin enforcing that the current user has one of the required roles."""

    required_roles: tuple[str, ...] = tuple()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not self.required_roles:
            raise ValueError("RoleRequiredMixin requires `required_roles` to be set.")
        if user_has_role(request.user, self.required_roles):
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "You do not have permission to access this resource.")
        return redirect(reverse("accounts:login"))


def role_required(*roles: str) -> Callable:
    """Function-based view decorator for role enforcement."""

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            if user_has_role(request.user, roles):
                return view_func(request, *args, **kwargs)
            messages.error(request, "You do not have permission to access this resource.")
            return redirect(reverse("accounts:login"))

        return _wrapped_view

    return decorator
