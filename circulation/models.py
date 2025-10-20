from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from catalog.models import Book, BookCopy


class Loan(models.Model):
	class Status(models.TextChoices):
		ACTIVE = "ACTIVE", "Active"
		OVERDUE = "OVERDUE", "Overdue"
		RETURNED = "RETURNED", "Returned"

	copy = models.ForeignKey(BookCopy, on_delete=models.PROTECT, related_name="loans")
	borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loans")
	issued_by = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="issued_loans",
	)
	issued_at = models.DateTimeField(default=timezone.now)
	due_at = models.DateTimeField()
	returned_at = models.DateTimeField(null=True, blank=True)
	status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
	fine_accrued = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ["-issued_at"]
		constraints = [
			models.UniqueConstraint(
				fields=["copy"],
				condition=Q(returned_at__isnull=True),
				name="unique_active_loan_per_copy",
			)
		]

	def __str__(self) -> str:
		return f"Loan of {self.copy} to {self.borrower}"

	def save(self, *args, **kwargs):
		is_new = self._state.adding
		if not self.due_at:
			self.due_at = self.issued_at + timezone.timedelta(days=settings.LOAN_PERIOD_DAYS)

		self.status = self._determine_status()
		super().save(*args, **kwargs)
		if is_new:
			self.copy.status = BookCopy.Status.ON_LOAN
			self.copy.save(update_fields=["status"])
		elif self.status == self.Status.RETURNED:
			self.copy.status = BookCopy.Status.AVAILABLE
			self.copy.save(update_fields=["status"])

	def _determine_status(self) -> str:
		if self.returned_at:
			return self.Status.RETURNED
		if timezone.now() > self.due_at:
			return self.Status.OVERDUE
		return self.Status.ACTIVE

	def mark_returned(self, return_time: Optional[timezone.datetime] = None) -> None:
		self.returned_at = return_time or timezone.now()
		self.status = self.Status.RETURNED
		self.save(update_fields=["returned_at", "status"])

	def calculate_overdue_fine(self) -> Decimal:
		if not self.returned_at and timezone.now() <= self.due_at:
			return Decimal("0.00")
		end_date = self.returned_at or timezone.now()
		overdue_days = max((end_date - self.due_at).days, 0)
		fine = Decimal(str(settings.FINE_RATE_PER_DAY)) * Decimal(overdue_days)
		self.fine_accrued = fine
		self.save(update_fields=["fine_accrued"])
		return fine

	def get_absolute_url(self):
		return reverse("circulation:loan-detail", args=[self.pk])


class Reservation(models.Model):
	class Status(models.TextChoices):
		PENDING = "PENDING", "Pending"
		NOTIFIED = "NOTIFIED", "Notified"
		CANCELLED = "CANCELLED", "Cancelled"
		FULFILLED = "FULFILLED", "Fulfilled"

	book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reservations")
	member = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reservations")
	created_at = models.DateTimeField(auto_now_add=True)
	expires_at = models.DateTimeField(null=True, blank=True)
	fulfilled_at = models.DateTimeField(null=True, blank=True)
	status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
	position = models.PositiveIntegerField(default=1)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ["created_at"]
		unique_together = ("book", "member", "status")

	def __str__(self) -> str:
		return f"Reservation for {self.book} by {self.member}"

	def save(self, *args, **kwargs):
		if self._state.adding and not self.position:
			next_position = (
				Reservation.objects.filter(book=self.book, status=self.Status.PENDING)
				.exclude(pk=self.pk)
				.count()
				+ 1
			)
			self.position = next_position
		super().save(*args, **kwargs)

	def mark_notified(self):
		self.status = self.Status.NOTIFIED
		self.expires_at = timezone.now() + timezone.timedelta(days=2)
		self.save(update_fields=["status", "expires_at"])

	def mark_fulfilled(self):
		self.status = self.Status.FULFILLED
		self.fulfilled_at = timezone.now()
		self.save(update_fields=["status", "fulfilled_at"])

	def cancel(self):
		self.status = self.Status.CANCELLED
		self.save(update_fields=["status"])


class Fine(models.Model):
	member = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fines")
	loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="fines")
	amount = models.DecimalField(max_digits=8, decimal_places=2)
	issued_at = models.DateTimeField(auto_now_add=True)
	paid_at = models.DateTimeField(null=True, blank=True)
	is_paid = models.BooleanField(default=False)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ["-issued_at"]

	def __str__(self) -> str:
		return f"Fine {self.amount} for {self.member}"

	def mark_paid(self):
		self.is_paid = True
		self.paid_at = timezone.now()
		self.save(update_fields=["is_paid", "paid_at"])
