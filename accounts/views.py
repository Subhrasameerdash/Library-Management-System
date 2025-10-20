from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import MemberProfileForm, UserLoginForm, UserRegistrationForm
from .models import MemberProfile, User
from .permissions import RoleRequiredMixin, role_required


class UserLoginView(LoginView):
	template_name = "accounts/login.html"
	authentication_form = UserLoginForm
	redirect_authenticated_user = True

	def get_success_url(self) -> str:
		redirect_to = self.get_redirect_url()
		if redirect_to:
			return redirect_to
		user: User = self.request.user
		if user.is_admin or user.is_librarian:
			return reverse("reports:dashboard")
		return reverse("accounts:overview")


class UserLogoutView(LogoutView):
	next_page = reverse_lazy("accounts:login")


class UserRegisterView(CreateView):
	model = User
	form_class = UserRegistrationForm
	template_name = "accounts/register.html"
	success_url = reverse_lazy("accounts:login")

	def form_valid(self, form: UserRegistrationForm) -> HttpResponse:
		user: User = form.save(commit=False)
		requested_role = form.cleaned_data.get("role", User.Role.MEMBER)

		if self.request.user.is_authenticated and self.request.user.is_admin:
			user.role = requested_role
			user.is_staff = requested_role in {
				User.Role.ADMIN,
				User.Role.LIBRARIAN,
			}
		else:
			user.role = User.Role.MEMBER

		user.save()
		messages.success(self.request, "Account created successfully. You can now log in.")
		self.object = user
		return redirect(self.get_success_url())


@method_decorator(login_required, name="dispatch")
class ProfileDetailView(DetailView):
	model = User
	template_name = "accounts/profile_detail.html"
	context_object_name = "profile_user"

	def get_object(self, queryset=None):
		return self.request.user


class ProfileUpdateView(UpdateView):
	model = MemberProfile
	form_class = MemberProfileForm
	template_name = "accounts/profile_form.html"
	success_url = reverse_lazy("accounts:profile")

	def get_object(self, queryset=None):
		return self.request.user.profile

	def form_valid(self, form: MemberProfileForm) -> HttpResponse:
		messages.success(self.request, "Profile updated successfully.")
		return super().form_valid(form)


class UserListView(RoleRequiredMixin, ListView):
	model = User
	template_name = "accounts/user_list.html"
	context_object_name = "users"
	paginate_by = 20
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def get_queryset(self):
		queryset = super().get_queryset().select_related("profile")
		role = self.request.GET.get("role")
		if role:
			queryset = queryset.filter(role=role)
		search = self.request.GET.get("q")
		if search:
			queryset = queryset.filter(
				Q(username__icontains=search)
				| Q(email__icontains=search)
				| Q(first_name__icontains=search)
				| Q(last_name__icontains=search)
			)
		return queryset.order_by("role", "username")


@role_required(User.Role.ADMIN, User.Role.LIBRARIAN)
def switch_user_role(request: HttpRequest, user_id: int, role: str) -> HttpResponse:
	target_role = role.upper()
	if target_role not in dict(User.Role.choices):
		messages.error(request, "Invalid role selection.")
		return redirect("accounts:user-list")

	user = User.objects.get(pk=user_id)
	user.role = target_role
	user.is_staff = target_role in {User.Role.ADMIN, User.Role.LIBRARIAN}
	user.save(update_fields=["role", "is_staff"])
	messages.success(request, f"Updated {user.username}'s role to {user.get_role_display()}.")
	return redirect("accounts:user-list")


@login_required
def account_overview(request: HttpRequest) -> HttpResponse:
	profile = getattr(request.user, "profile", None)
	return render(
		request,
		"accounts/account_overview.html",
		{
			"profile": profile,
			"loans": request.user.loans.select_related("copy", "copy__book")[:5],
			"reservations": request.user.reservations.select_related("book")[:5],
		},
	)
