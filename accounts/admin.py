from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import MemberProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	"""Customize the user admin to expose role-based controls."""

	fieldsets = DjangoUserAdmin.fieldsets + (
		(
			"Role & Profile",
			{
				"fields": (
					"role",
					"employee_id",
					"avatar",
				)
			},
		),
	)
	list_display = ("username", "email", "role", "is_active", "is_staff")
	list_filter = ("role", "is_active", "is_staff")
	search_fields = ("username", "email", "first_name", "last_name", "employee_id")


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "membership_id", "phone_number", "joined_at")
	search_fields = ("user__username", "membership_id", "phone_number")
	autocomplete_fields = ("user", "preferred_categories")
