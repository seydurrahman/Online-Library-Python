from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Category, Review, Book, Shelf, Rack, Serial

User = get_user_model()


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["comment", "rating"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4}),
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
        }


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "category",
            "shelf",
            "rack",
            "serial",
            "cover",
            "description",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "author": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "shelf": forms.Select(attrs={"class": "form-select"}),
            "rack": forms.Select(attrs={"class": "form-select"}),
            "serial": forms.Select(attrs={"class": "form-select"}),
            "cover": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class SelfRackForm(forms.Form):
    self_name = forms.CharField(max_length=100, label="Self name")
    rack_number = forms.CharField(max_length=50, label="Rack number")
    serial_number = forms.CharField(
        max_length=50, label="Serial number", required=False
    )
    side_name = forms.CharField(max_length=50, label="Side", required=False)


class RackForm(forms.ModelForm):
    # allow editing serials as a comma/newline-separated string
    serials = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Enter serial numbers separated by commas or new lines",
        label="Serial numbers",
    )

    class Meta:
        model = Rack
        fields = ["shelf", "rack_number", "side_name"]
