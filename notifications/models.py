from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone


class Notification(models.Model):
	class Category(models.TextChoices):
		DUE_REMINDER = "DUE_REMINDER", "Due reminder"
		RESERVATION = "RESERVATION", "Reservation"
		FINE = "FINE", "Fine"
		GENERAL = "GENERAL", "General"

	recipient = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="notifications",
	)
	category = models.CharField(max_length=30, choices=Category.choices, default=Category.GENERAL)
	subject = models.CharField(max_length=255)
	message = models.TextField()
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	sent_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"Notification to {self.recipient} - {self.subject}"

	def mark_read(self):
		self.is_read = True
		self.save(update_fields=["is_read"])

	def dispatch_email(self):
		send_mail(
			subject=self.subject,
			message=self.message,
			from_email=settings.DEFAULT_FROM_EMAIL,
			recipient_list=[self.recipient.email],
			fail_silently=True,
		)
		self.sent_at = timezone.now()
		self.save(update_fields=["sent_at"])


class NotificationPreference(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_pref")
	receive_email = models.BooleanField(default=True)
	receive_push = models.BooleanField(default=False)
	daily_digest = models.BooleanField(default=True)

	def __str__(self) -> str:
		return f"Notification preferences for {self.user}"
