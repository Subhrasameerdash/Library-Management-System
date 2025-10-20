from __future__ import annotations

from django import forms

import django_filters
from django_filters.widgets import RangeWidget

from .models import Book, Category


class BookFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    author = django_filters.CharFilter(lookup_expr="icontains")
    isbn = django_filters.CharFilter(lookup_expr="icontains")
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all(), field_name="category")
    publication_date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Book
        fields = ["title", "author", "isbn", "category", "publication_date"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.form.fields.values():
            widget = field.widget
            existing = widget.attrs.get("class", "")
            if isinstance(widget, RangeWidget):
                # Date range renders as a pair of inputs; apply to each child widget.
                for sub_widget in widget.widgets:
                    classes = sub_widget.attrs.get("class", "")
                    sub_widget.attrs["class"] = f"{classes} form-control".strip()
            elif isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.RadioSelect)):
                widget.attrs["class"] = f"{existing} form-check-input".strip()
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = f"{existing} form-select".strip()
            else:
                widget.attrs["class"] = f"{existing} form-control".strip()
