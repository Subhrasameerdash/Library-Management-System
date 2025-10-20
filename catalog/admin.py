from django.contrib import admin

from .models import Book, BookCopy, Category


class BookCopyInline(admin.TabularInline):
	model = BookCopy
	extra = 0
	fields = ("barcode", "status", "location", "acquired_at")
	readonly_fields = ("acquired_at",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	prepopulated_fields = {"slug": ("name",)}
	search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
	list_display = ("title", "author", "isbn", "category", "available_copies", "total_copies")
	search_fields = ("title", "author", "isbn")
	list_filter = ("category", "publication_date")
	inlines = [BookCopyInline]


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
	list_display = ("book", "barcode", "status", "location", "acquired_at")
	list_filter = ("status", "book__category")
	search_fields = ("barcode", "book__title", "book__author")
