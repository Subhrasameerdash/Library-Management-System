from django.contrib import admin

from .models import Fine, Loan, Reservation


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
	list_display = (
		"copy",
		"borrower",
		"issued_at",
		"due_at",
		"returned_at",
		"status",
		"fine_accrued",
	)
	list_filter = ("status", "issued_at", "due_at")
	search_fields = ("copy__barcode", "copy__book__title", "borrower__username")
	autocomplete_fields = ("copy", "borrower", "issued_by")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
	list_display = ("book", "member", "status", "created_at", "position")
	list_filter = ("status", "created_at")
	search_fields = ("book__title", "member__username")


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
	list_display = ("member", "loan", "amount", "is_paid", "issued_at")
	list_filter = ("is_paid", "issued_at")
	search_fields = ("member__username", "loan__copy__book__title")
