from __future__ import annotations

import csv
from datetime import datetime

from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView, View

from accounts.models import User
from accounts.permissions import RoleRequiredMixin
from catalog.models import Book
from circulation.models import Fine, Loan, Reservation


class DashboardView(RoleRequiredMixin, TemplateView):
	template_name = "reports/dashboard.html"
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.update(
			{
				"total_books": Book.objects.count(),
				"total_members": User.objects.filter(role=User.Role.MEMBER).count(),
				"active_loans": Loan.objects.filter(returned_at__isnull=True).count(),
				"overdue_loans": Loan.objects.filter(status=Loan.Status.OVERDUE).count(),
				"reservations": Reservation.objects.filter(status=Reservation.Status.PENDING).count(),
				"outstanding_fines": Fine.objects.filter(is_paid=False).count(),
				"recent_loans": Loan.objects.select_related("copy__book", "borrower")[:5],
				"top_categories": self._top_categories(),
			}
		)
		return context

	def _top_categories(self):
		return (
			Book.objects.values("category__name")
			.annotate(total=Count("id"))
			.order_by("-total")[:5]
		)


class LoanCSVExportView(RoleRequiredMixin, View):
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def get(self, request: HttpRequest) -> HttpResponse:
		response = HttpResponse(content_type="text/csv")
		filename = f"loans_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
		response["Content-Disposition"] = f"attachment; filename={filename}"
		writer = csv.writer(response)
		writer.writerow(["Book", "Borrower", "Issued", "Due", "Returned", "Status", "Fine"])
		for loan in Loan.objects.select_related("copy__book", "borrower"):
			writer.writerow(
				[
					loan.copy.book.title,
					loan.borrower.username,
					loan.issued_at.strftime("%Y-%m-%d"),
					loan.due_at.strftime("%Y-%m-%d"),
					loan.returned_at.strftime("%Y-%m-%d") if loan.returned_at else "",
					loan.get_status_display(),
					loan.fine_accrued,
				]
			)
		return response
