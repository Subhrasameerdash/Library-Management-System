from __future__ import annotations

from django.shortcuts import redirect


def home_redirect(request):
    if request.user.is_authenticated:
        if getattr(request.user, "is_admin", False) or getattr(request.user, "is_librarian", False):
            return redirect("reports:dashboard")
        return redirect("accounts:overview")
    return redirect("catalog:book-list")
