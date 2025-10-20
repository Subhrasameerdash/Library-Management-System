import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def generate_membership_id() -> str:
	"""Return a short, unique membership identifier."""

	return uuid.uuid4().hex[:12].upper()


class User(AbstractUser):
	"""Custom user model with support for application roles."""

	class Role(models.TextChoices):
		ADMIN = "ADMIN", _("Administrator")
		LIBRARIAN = "LIBRARIAN", _("Librarian")
		MEMBER = "MEMBER", _("Member / Student")

	role = models.CharField(
		max_length=20,
		choices=Role.choices,
		default=Role.MEMBER,
		help_text=_("Determines the permissions granted to the user."),
	)
	employee_id = models.CharField(
		max_length=50,
		blank=True,
		help_text=_("Optional staff identifier for administrators and librarians."),
	)
	avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta(AbstractUser.Meta):
		ordering = ["username"]

	@property
	def is_admin(self) -> bool:
		return self.is_superuser or self.role == self.Role.ADMIN

	@property
	def is_librarian(self) -> bool:
		return self.role == self.Role.LIBRARIAN

	@property
	def is_member(self) -> bool:
		return self.role == self.Role.MEMBER

	def get_absolute_url(self):
		return reverse("accounts:detail", args=[self.pk])


class MemberProfile(models.Model):
	"""Extended profile data for member accounts."""

	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="profile",
	)
	membership_id = models.CharField(
		max_length=12,
		unique=True,
		default=generate_membership_id,
	)
	phone_regex = RegexValidator(
		regex=r"^\+?[0-9]{7,15}$",
		message=_("Enter a valid phone number with up to 15 digits."),
	)
	phone_number = models.CharField(
		validators=[phone_regex],
		max_length=17,
		blank=True,
	)
	address = models.TextField(blank=True)
	city = models.CharField(max_length=120, blank=True)
	date_of_birth = models.DateField(blank=True, null=True)
	joined_at = models.DateTimeField(default=timezone.now)
	preferred_categories = models.ManyToManyField(
		"catalog.Category",
		related_name="members",
		blank=True,
	)

	class Meta:
		ordering = ["user__username"]
		verbose_name = _("Member profile")
		verbose_name_plural = _("Member profiles")

	def __str__(self) -> str:
		return f"{self.user.get_full_name() or self.user.username} ({self.membership_id})"

	def get_absolute_url(self):
		return reverse("accounts:profile", args=[self.user.pk])
