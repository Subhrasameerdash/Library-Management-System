from __future__ import annotations

from rest_framework import serializers

from accounts.models import MemberProfile, User
from catalog.models import Book, BookCopy, Category
from circulation.models import Fine, Loan, Reservation


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description")


class BookCopySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCopy
        fields = ("id", "barcode", "status", "location", "acquired_at")


class BookSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )
    available_copies = serializers.IntegerField(read_only=True)
    total_copies = serializers.IntegerField(read_only=True)
    copies = BookCopySerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "isbn",
            "category",
            "category_id",
            "publication_date",
            "publisher",
            "description",
            "language",
            "cover_image",
            "tags",
            "available_copies",
            "total_copies",
            "copies",
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role")


class MemberProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    preferred_categories = CategorySerializer(many=True, read_only=True)
    preferred_category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        source="preferred_categories",
        write_only=True,
        required=False,
    )

    class Meta:
        model = MemberProfile
        fields = (
            "membership_id",
            "phone_number",
            "address",
            "city",
            "date_of_birth",
            "joined_at",
            "preferred_categories",
            "preferred_category_ids",
            "user",
        )


class LoanSerializer(serializers.ModelSerializer):
    borrower = UserSerializer(read_only=True)
    borrower_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="borrower", write_only=True
    )
    copy = BookCopySerializer(read_only=True)
    copy_id = serializers.PrimaryKeyRelatedField(
        queryset=BookCopy.objects.all(), source="copy", write_only=True
    )

    class Meta:
        model = Loan
        fields = (
            "id",
            "copy",
            "copy_id",
            "borrower",
            "borrower_id",
            "issued_at",
            "due_at",
            "returned_at",
            "status",
            "fine_accrued",
            "notes",
        )


class ReservationSerializer(serializers.ModelSerializer):
    member = UserSerializer(read_only=True)
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="member", write_only=True
    )
    book = BookSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(), source="book", write_only=True
    )

    class Meta:
        model = Reservation
        fields = (
            "id",
            "book",
            "book_id",
            "member",
            "member_id",
            "status",
            "created_at",
            "expires_at",
            "fulfilled_at",
            "position",
        )


class FineSerializer(serializers.ModelSerializer):
    member = UserSerializer(read_only=True)
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="member", write_only=True
    )
    loan = LoanSerializer(read_only=True)
    loan_id = serializers.PrimaryKeyRelatedField(
        queryset=Loan.objects.all(), source="loan", write_only=True
    )

    class Meta:
        model = Fine
        fields = (
            "id",
            "loan",
            "loan_id",
            "member",
            "member_id",
            "amount",
            "issued_at",
            "is_paid",
            "paid_at",
            "notes",
        )
