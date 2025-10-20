from __future__ import annotations

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
	name = models.CharField(max_length=150, unique=True)
	slug = models.SlugField(max_length=160, unique=True, blank=True)
	description = models.TextField(blank=True)

	class Meta:
		ordering = ["name"]
		verbose_name_plural = "categories"

	def __str__(self) -> str:
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	def get_absolute_url(self):
		return reverse("catalog:category-detail", args=[self.slug])


class Book(models.Model):
	title = models.CharField(max_length=255)
	author = models.CharField(max_length=255)
	isbn = models.CharField(max_length=13, unique=True)
	category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="books")
	publication_date = models.DateField(blank=True, null=True)
	publisher = models.CharField(max_length=255, blank=True)
	description = models.TextField(blank=True)
	cover_image = models.ImageField(upload_to="book_covers/", blank=True, null=True)
	language = models.CharField(max_length=60, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	tags = models.JSONField(default=list, blank=True)

	class Meta:
		ordering = ["title"]
		indexes = [
			models.Index(fields=["title"]),
			models.Index(fields=["author"]),
			models.Index(fields=["isbn"]),
		]

	def __str__(self) -> str:
		return f"{self.title} ({self.isbn})"

	def get_absolute_url(self):
		return reverse("catalog:book-detail", args=[self.pk])

	@property
	def total_copies(self) -> int:
		return getattr(self, "_total_copies", self.copies.count())

	@total_copies.setter
	def total_copies(self, value: int) -> None:
		self._total_copies = value

	@property
	def available_copies(self) -> int:
		return self.copies.filter(status=BookCopy.Status.AVAILABLE).count()


class BookCopy(models.Model):
	class Status(models.TextChoices):
		AVAILABLE = "AVAILABLE", _("Available")
		ON_LOAN = "ON_LOAN", _("On loan")
		RESERVED = "RESERVED", _("Reserved")
		MAINTENANCE = "MAINTENANCE", _("Maintenance")
		LOST = "LOST", _("Lost")

	book = models.ForeignKey(Book, related_name="copies", on_delete=models.CASCADE)
	barcode = models.CharField(max_length=24, unique=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
	location = models.CharField(max_length=120, blank=True)
	acquired_at = models.DateField(default=timezone.now)
	notes = models.TextField(blank=True)

	class Meta:
		unique_together = ("book", "barcode")
		ordering = ["book", "barcode"]

	def __str__(self) -> str:
		return f"{self.book.title} - {self.barcode}"

	def mark_available(self):
		self.status = self.Status.AVAILABLE
		self.save(update_fields=["status"])

	def is_available(self) -> bool:
		return self.status == self.Status.AVAILABLE
