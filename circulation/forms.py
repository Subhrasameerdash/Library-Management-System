from __future__ import annotations

from django import forms

from catalog.models import Book, BookCopy

from .models import Fine, Loan, Reservation


def _bootstrap_class(widget: forms.Widget) -> str:
    if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.RadioSelect)):
        return "form-check-input"
    if isinstance(widget, (forms.Select, forms.SelectMultiple)):
        return "form-select"
    return "form-control"


class LoanForm(forms.ModelForm):
    due_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        required=False,
        help_text="Leave blank to use the default loan period.",
    )

    class Meta:
        model = Loan
        fields = ("copy", "borrower", "issued_by", "due_at", "notes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        available_copies = BookCopy.objects.filter(status=BookCopy.Status.AVAILABLE)
        self.fields["copy"].queryset = available_copies.select_related("book")
        for field in self.fields.values():
            css_class = _bootstrap_class(field.widget)
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()


class LoanReturnForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ("returned_at", "notes")
        widgets = {
            "returned_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = _bootstrap_class(field.widget)
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ("book", "member", "notes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["book"].queryset = Book.objects.all().order_by("title")
        for field in self.fields.values():
            css_class = _bootstrap_class(field.widget)
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()


class FineForm(forms.ModelForm):
    class Meta:
        model = Fine
        fields = ("loan", "member", "amount", "notes", "is_paid")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["loan"].queryset = Loan.objects.select_related("borrower", "copy")
        for field in self.fields.values():
            css_class = _bootstrap_class(field.widget)
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()
