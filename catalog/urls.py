from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.BookListView.as_view(), name="book-list"),
    path("books/<int:pk>/", views.BookDetailView.as_view(), name="book-detail"),
    path("books/create/", views.BookCreateView.as_view(), name="book-create"),
    path("books/<int:pk>/edit/", views.BookUpdateView.as_view(), name="book-edit"),
    path("books/<int:pk>/delete/", views.BookDeleteView.as_view(), name="book-delete"),
    path(
        "books/<int:book_id>/copies/add/",
        views.BookCopyCreateView.as_view(),
        name="bookcopy-add",
    ),
    path(
        "copies/<int:pk>/edit/",
        views.BookCopyUpdateView.as_view(),
        name="bookcopy-edit",
    ),
    path(
        "copies/<int:pk>/delete/",
        views.BookCopyDeleteView.as_view(),
        name="bookcopy-delete",
    ),
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("categories/<slug:slug>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("books/<int:book_id>/toggle-favorite/", views.toggle_favorite, name="toggle-favorite"),
]
