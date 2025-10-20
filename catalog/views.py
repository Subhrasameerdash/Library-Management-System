from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.models import User
from accounts.permissions import RoleRequiredMixin

from .filters import BookFilter
from .forms import BookCopyForm, BookForm
from .models import Book, BookCopy, Category


@method_decorator(login_required, name="dispatch")
class BookListView(ListView):
	model = Book
	template_name = "catalog/book_list.html"
	paginate_by = 12

	def get_queryset(self):
		queryset = (
			Book.objects.select_related("category")
			.annotate(total_copies=Count("copies"))
			.order_by("title")
		)
		self.filterset = BookFilter(self.request.GET or None, queryset=queryset)
		search = self.request.GET.get("q")
		filtered_qs = self.filterset.qs
		if search:
			filtered_qs = filtered_qs.filter(
				Q(title__icontains=search)
				| Q(author__icontains=search)
				| Q(isbn__icontains=search)
				| Q(category__name__icontains=search)
			)
		return filtered_qs

	def get_context_data(self, **kwargs: Any):
		context = super().get_context_data(**kwargs)
		context["filter"] = self.filterset
		context["search_query"] = self.request.GET.get("q", "")
		return context


@method_decorator(login_required, name="dispatch")
class BookDetailView(DetailView):
	model = Book
	template_name = "catalog/book_detail.html"

	def get_queryset(self):
		return Book.objects.select_related("category").prefetch_related("copies")


class BookCreateView(RoleRequiredMixin, CreateView):
	model = Book
	form_class = BookForm
	template_name = "catalog/book_form.html"
	success_url = reverse_lazy("catalog:book-list")
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def form_valid(self, form: BookForm) -> HttpResponse:
		messages.success(self.request, "Book created successfully.")
		return super().form_valid(form)


class BookUpdateView(RoleRequiredMixin, UpdateView):
	model = Book
	form_class = BookForm
	template_name = "catalog/book_form.html"
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def get_success_url(self):
		messages.success(self.request, "Book updated successfully.")
		return reverse("catalog:book-detail", args=[self.object.pk])


class BookDeleteView(RoleRequiredMixin, DeleteView):
	model = Book
	template_name = "catalog/book_confirm_delete.html"
	success_url = reverse_lazy("catalog:book-list")
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def delete(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
		messages.success(request, "Book deleted.")
		return super().delete(request, *args, **kwargs)


class BookCopyCreateView(RoleRequiredMixin, CreateView):
	model = BookCopy
	form_class = BookCopyForm
	template_name = "catalog/bookcopy_form.html"
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def dispatch(self, request: HttpRequest, *args, **kwargs):
		self.book = get_object_or_404(Book, pk=kwargs.get("book_id"))
		return super().dispatch(request, *args, **kwargs)

	def form_valid(self, form: BookCopyForm) -> HttpResponse:
		form.instance.book = self.book
		messages.success(self.request, "Book copy added to inventory.")
		return super().form_valid(form)

	def get_success_url(self):
		return self.book.get_absolute_url()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["book"] = self.book
		return context


class BookCopyUpdateView(RoleRequiredMixin, UpdateView):
	model = BookCopy
	form_class = BookCopyForm
	template_name = "catalog/bookcopy_form.html"
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def form_valid(self, form: BookCopyForm) -> HttpResponse:
		messages.success(self.request, "Book copy updated.")
		return super().form_valid(form)

	def get_success_url(self):
		return self.object.book.get_absolute_url()


class BookCopyDeleteView(RoleRequiredMixin, DeleteView):
	model = BookCopy
	template_name = "catalog/bookcopy_confirm_delete.html"
	required_roles = (User.Role.ADMIN, User.Role.LIBRARIAN)

	def delete(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
		self.object = self.get_object()
		book = self.object.book
		response = super().delete(request, *args, **kwargs)
		messages.success(request, "Book copy removed from inventory.")
		return redirect(book.get_absolute_url())


@method_decorator(login_required, name="dispatch")
class CategoryListView(ListView):
	model = Category
	template_name = "catalog/category_list.html"
	context_object_name = "categories"


@method_decorator(login_required, name="dispatch")
class CategoryDetailView(DetailView):
	model = Category
	template_name = "catalog/category_detail.html"
	slug_field = "slug"
	slug_url_kwarg = "slug"
	context_object_name = "category"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["books"] = self.object.books.all()
		return context


@login_required
def toggle_favorite(request: HttpRequest, book_id: int) -> HttpResponse:
	book = get_object_or_404(Book, pk=book_id)
	profile = getattr(request.user, "profile", None)
	if profile:
		if book.category in profile.preferred_categories.all():
			profile.preferred_categories.remove(book.category)
			messages.info(request, "Removed category from preferences.")
		else:
			profile.preferred_categories.add(book.category)
			messages.success(request, "Added category to your preferences.")
	return redirect(book.get_absolute_url())
