from __future__ import annotations

from django import forms

from .models import Book, BookCopy


def _bootstrap_class(widget: forms.Widget) -> str:
    if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.RadioSelect)):
        return "form-check-input"
    if isinstance(widget, (forms.Select, forms.SelectMultiple)):
        return "form-select"
    return "form-control"


class BookForm(forms.ModelForm):
    publication_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = Book
        fields = (
            "title",
            "author",
            "isbn",
            "category",
            "publication_date",
            "publisher",
            "language",
            "description",
            "cover_image",
            "tags",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "tags": forms.TextInput(attrs={"placeholder": "Comma separated"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = _bootstrap_class(field.widget)
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()


class BookCopyForm(forms.ModelForm):
    acquired_at = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )

    class Meta:
        model = BookCopy
        fields = (
            "barcode",
            "status",
            "location",
            "acquired_at",
            "notes",
        )
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = _bootstrap_class(field.widget)
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()
