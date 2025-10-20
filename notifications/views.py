from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView

from .models import Notification, NotificationPreference


@method_decorator(login_required, name="dispatch")
class NotificationListView(ListView):
	model = Notification
	template_name = "notifications/list.html"
	paginate_by = 20

	def get_queryset(self):
		return Notification.objects.filter(recipient=self.request.user)


@method_decorator(login_required, name="dispatch")
class NotificationPreferenceUpdateView(UpdateView):
	model = NotificationPreference
	fields = ("receive_email", "receive_push", "daily_digest")
	template_name = "notifications/preferences_form.html"
	success_url = reverse_lazy("notifications:list")

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		for field in form.fields.values():
			existing = field.widget.attrs.get("class", "")
			field.widget.attrs["class"] = f"{existing} form-check-input".strip()
		return form

	def get_object(self, queryset=None):
		preference, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
		return preference

	def form_valid(self, form):
		messages.success(self.request, "Notification preferences updated.")
		return super().form_valid(form)


@login_required
def mark_notification_read(request: HttpRequest, pk: int) -> HttpResponse:
	notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
	notification.mark_read()
	messages.info(request, "Notification marked as read.")
	return redirect("notifications:list")
