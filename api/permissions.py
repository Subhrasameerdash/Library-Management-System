from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrLibrarian(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_admin or user.is_librarian))


class IsAdminLibrarianOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and (user.is_admin or user.is_librarian))
