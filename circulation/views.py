from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from accounts.models import User
from accounts.permissions import RoleRequiredMixin

from .forms import FineForm, LoanForm, LoanReturnForm, ReservationForm
from .models import Fine, Loan, Reservation


@method_decorator(login_required, name="dispatch")
class LoanListView(ListView):
	model = Loan
	template_name = "circulation/loan_list.html"
	paginate_by = 20

	def get_queryset(self):
		queryset = (
			Loan.objects.select_related("copy", "copy__book", "borrower", "issued_by")
			.annotate(fine_count=Count("fines"))
			.order_by("-issued_at")
		)
		if self.request.user.is_member:
			queryset = queryset.filter(borrower=self.request.user)
		search = self.request.GET.get("q")
		if search:
			queryset = queryset.filter(
				Q(copy__book__title__icontains=search)
				| Q(borrower__username__icontains=search)
				| Q(copy__barcode__icontains=search)
			)
		status = self.request.GET.get("status")
		if status:
			queryset = queryset.filter(status=status)
		return queryset


@method_decorator(login_required, name="dispatch")
class LoanDetailView(DetailView):
	model = Loan
	template_name = "circulation/loan_detail.html"

	def get_queryset(self):
		queryset = Loan.objects.select_related("copy", "copy__book", "borrower", "issued_by")
		if self.request.user.is_member:
			queryset = queryset.filter(borrower=self.request.user)
		return queryset


class LoanCreateView(RoleRequiredMixin, CreateView):
	model = Loan
	form_class = LoanForm
	template_name = "circulation/loan_form.html"
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)
	success_url = reverse_lazy("circulation:loan-list")

	def form_valid(self, form: LoanForm) -> HttpResponse:
		borrower = form.cleaned_data["borrower"]
		active_loans = Loan.objects.filter(borrower=borrower, returned_at__isnull=True).count()
		if active_loans >= settings.MAX_ACTIVE_LOANS_PER_MEMBER:
			form.add_error(
				"borrower",
				f"Member has reached the maximum of {settings.MAX_ACTIVE_LOANS_PER_MEMBER} active loans.",
			)
			return self.form_invalid(form)
		if not form.cleaned_data.get("due_at"):
			form.instance.due_at = timezone.now() + timezone.timedelta(days=settings.LOAN_PERIOD_DAYS)
		if not form.cleaned_data.get("issued_by"):
			form.instance.issued_by = self.request.user
		messages.success(self.request, "Loan created successfully.")
		return super().form_valid(form)


class LoanReturnView(RoleRequiredMixin, UpdateView):
	model = Loan
	form_class = LoanReturnForm
	template_name = "circulation/loan_return_form.html"
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def form_valid(self, form: LoanReturnForm) -> HttpResponse:
		loan = form.save(commit=False)
		loan.status = Loan.Status.RETURNED
		if not loan.returned_at:
			loan.returned_at = timezone.now()
		loan.save(update_fields=["returned_at", "status", "notes"])
		loan.copy.status = loan.copy.Status.AVAILABLE
		loan.copy.save(update_fields=["status"])
		messages.success(self.request, "Loan marked as returned.")
		return redirect(loan.get_absolute_url())


class ReservationListView(RoleRequiredMixin, ListView):
	model = Reservation
	template_name = "circulation/reservation_list.html"
	paginate_by = 20
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def get_queryset(self):
		queryset = Reservation.objects.select_related("book", "member").order_by("status", "position")
		status = self.request.GET.get("status")
		if status:
			queryset = queryset.filter(status=status)
		return queryset


class ReservationCreateView(RoleRequiredMixin, CreateView):
	model = Reservation
	form_class = ReservationForm
	template_name = "circulation/reservation_form.html"
	success_url = reverse_lazy("circulation:reservation-list")
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def form_valid(self, form: ReservationForm) -> HttpResponse:
		messages.success(self.request, "Reservation added to waitlist.")
		return super().form_valid(form)


class ReservationUpdateView(RoleRequiredMixin, UpdateView):
	model = Reservation
	form_class = ReservationForm
	template_name = "circulation/reservation_form.html"
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def form_valid(self, form: ReservationForm) -> HttpResponse:
		messages.success(self.request, "Reservation updated.")
		return super().form_valid(form)


@login_required
def my_reservations(request: HttpRequest) -> HttpResponse:
	reservations = (
		Reservation.objects.filter(member=request.user)
		.select_related("book")
		.order_by("status", "created_at")
	)
	return render(request, "circulation/my_reservations.html", {"reservations": reservations})


class ReservationStatusView(RoleRequiredMixin, View):
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def post(self, request: HttpRequest, pk: int, action: str) -> HttpResponse:
		reservation = get_object_or_404(Reservation, pk=pk)
		if action == "notify":
			reservation.mark_notified()
			messages.success(request, "Member notified about availability.")
		elif action == "fulfill":
			reservation.mark_fulfilled()
			messages.success(request, "Reservation fulfilled.")
		elif action == "cancel":
			reservation.cancel()
			messages.info(request, "Reservation cancelled.")
		return redirect("circulation:reservation-list")


class FineListView(RoleRequiredMixin, ListView):
	model = Fine
	template_name = "circulation/fine_list.html"
	paginate_by = 25
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def get_queryset(self):
		queryset = Fine.objects.select_related("member", "loan", "loan__copy", "loan__copy__book")
		status = self.request.GET.get("status")
		if status == "outstanding":
			queryset = queryset.filter(is_paid=False)
		elif status == "paid":
			queryset = queryset.filter(is_paid=True)
		return queryset.order_by("-issued_at")


class FineCreateView(RoleRequiredMixin, CreateView):
	model = Fine
	form_class = FineForm
	template_name = "circulation/fine_form.html"
	success_url = reverse_lazy("circulation:fine-list")
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def form_valid(self, form: FineForm) -> HttpResponse:
		messages.success(self.request, "Fine recorded successfully.")
		return super().form_valid(form)


class FineUpdateView(RoleRequiredMixin, UpdateView):
	model = Fine
	form_class = FineForm
	template_name = "circulation/fine_form.html"
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def form_valid(self, form: FineForm) -> HttpResponse:
		messages.success(self.request, "Fine updated successfully.")
		return super().form_valid(form)


@login_required
def pay_fine(request: HttpRequest, pk: int) -> HttpResponse:
	fine = get_object_or_404(Fine, pk=pk, member=request.user)
	if fine.is_paid:
		messages.info(request, "Fine already settled.")
	else:
		fine.mark_paid()
		messages.success(request, "Thank you! Fine has been marked as paid.")
	return redirect("circulation:my-fines")


@login_required
def my_fines(request: HttpRequest) -> HttpResponse:
	fines = Fine.objects.filter(member=request.user).order_by("is_paid", "-issued_at")
	outstanding_total = fines.filter(is_paid=False).aggregate(total=Sum("amount"))
	return render(
		request,
		"circulation/my_fines.html",
		{
			"fines": fines.select_related("loan", "loan__copy", "loan__copy__book"),
			"outstanding_total": outstanding_total["total"] or Decimal("0.00"),
		},
	)
