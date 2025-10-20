
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import MemberProfile, User


def _bootstrap_class(widget: forms.Widget) -> str:
    if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.RadioSelect)):
        return "form-check-input"
    if isinstance(widget, (forms.Select, forms.SelectMultiple)):
        return "form-select"
    return "form-control"


class UserRegistrationForm(UserCreationForm):
    """Registration form that captures role and contact details."""

    role = forms.ChoiceField(choices=User.Role.choices)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = _bootstrap_class(field.widget)
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()


class MemberProfileForm(forms.ModelForm):
    class Meta:
        model = MemberProfile
        fields = (
            "phone_number",
            "address",
            "city",
            "date_of_birth",
            "preferred_categories",
        )
        widgets = {
            "preferred_categories": forms.CheckboxSelectMultiple,
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = _bootstrap_class(field.widget)
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "placeholder": "Username",
                "class": "form-control",
            }
        )
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"placeholder": "Password", "class": "form-control"}
        ),
    )
