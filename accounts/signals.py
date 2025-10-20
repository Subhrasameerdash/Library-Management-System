from __future__ import annotations

from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MemberProfile, User


@receiver(post_save, sender=User)
def ensure_member_profile(sender: type[User], instance: User, created: bool, **_: Any) -> None:
	"""Create or update a member profile when a member account is saved."""

	if not created:
		if instance.is_member and not hasattr(instance, "profile"):
			MemberProfile.objects.create(user=instance)
		return

	if instance.is_member:
		MemberProfile.objects.create(user=instance)
