from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ("recipient", "subject", "category", "created_at", "is_read")
	list_filter = ("category", "is_read", "created_at")
	search_fields = ("subject", "recipient__username")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
	list_display = ("user", "receive_email", "receive_push", "daily_digest")
