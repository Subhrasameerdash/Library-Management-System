from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from catalog.models import Book
from circulation.models import Fine, Loan, Reservation

from .permissions import IsAdminLibrarianOrReadOnly, IsAdminOrLibrarian
from .serializers import (
	BookSerializer,
	FineSerializer,
	LoanSerializer,
	ReservationSerializer,
)


class BookViewSet(viewsets.ModelViewSet):
	queryset = Book.objects.prefetch_related("copies", "category")
	serializer_class = BookSerializer
	permission_classes = (IsAdminLibrarianOrReadOnly,)
	filterset_fields = ("category", "author", "language")
	search_fields = ("title", "author", "isbn")
	ordering_fields = ("title", "author", "publication_date")


class LoanViewSet(viewsets.ModelViewSet):
	queryset = Loan.objects.select_related("copy__book", "borrower", "issued_by")
	serializer_class = LoanSerializer
	filterset_fields = ("status", "borrower__id")
	search_fields = ("copy__book__title", "copy__barcode", "borrower__username")

	def get_queryset(self):
		queryset = self.queryset
		if not self.request.user.is_admin and not self.request.user.is_librarian:
			queryset = queryset.filter(borrower=self.request.user)
		return queryset

	def get_permissions(self):
		if self.request.method in SAFE_METHODS:
			return [IsAuthenticated()]
		return [IsAdminOrLibrarian()]

	@action(detail=True, methods=["post"], permission_classes=[IsAdminOrLibrarian])
	def mark_returned(self, request, pk=None):
		loan = self.get_object()
		loan.mark_returned()
		return Response(LoanSerializer(loan, context=self.get_serializer_context()).data)


class ReservationViewSet(viewsets.ModelViewSet):
	queryset = Reservation.objects.select_related("book", "member")
	serializer_class = ReservationSerializer
	filterset_fields = ("status",)

	def get_queryset(self):
		queryset = self.queryset
		if not self.request.user.is_admin and not self.request.user.is_librarian:
			queryset = queryset.filter(member=self.request.user)
		return queryset

	def get_permissions(self):
		if self.request.method in SAFE_METHODS or self.request.method == "POST":
			return [IsAuthenticated()]
		return [IsAdminOrLibrarian()]

	def perform_create(self, serializer):
		if self.request.user.is_admin or self.request.user.is_librarian:
			serializer.save()
		else:
			serializer.save(member=self.request.user)


class FineViewSet(viewsets.ModelViewSet):
	queryset = Fine.objects.select_related("loan__copy__book", "member")
	serializer_class = FineSerializer
	filterset_fields = ("is_paid",)

	def get_queryset(self):
		queryset = self.queryset
		if not self.request.user.is_admin and not self.request.user.is_librarian:
			queryset = queryset.filter(member=self.request.user)
		return queryset

	def get_permissions(self):
		if self.request.method in SAFE_METHODS:
			return [IsAuthenticated()]
		return [IsAdminOrLibrarian()]
