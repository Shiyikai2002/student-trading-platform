from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Item, CustomUser, Offer, UserRating
import re
from .models import Report
from django.contrib.auth.forms import UserChangeForm

# Custom user registration form with university email validation
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Use your university email (e.g., 2222222A@student.gla.ac.uk)."
    )

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]

    def clean_username(self):
        """Ensure username is alphanumeric and does not contain special characters."""
        username = self.cleaned_data.get("username")
        if not re.match(r"^[a-zA-Z0-9]+$", username):
            raise forms.ValidationError("Username can only contain letters and numbers.")
        return username

    def clean_email(self):
        """Validate that email follows the university format."""
        email = self.cleaned_data.get("email")
        if not re.match(r"^\d{7}[A-Z]@student\.gla\.ac\.uk$", email):
            raise forms.ValidationError("Invalid university email. Please use your @student.gla.ac.uk email.")
        return email


# Item Form for listing new products
class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'description', 'category', 'price', 'image']

    def clean_price(self):
        """Ensure the price is a positive value."""
        price = self.cleaned_data.get("price")
        if price <= 0:
            raise forms.ValidationError("Price must be a positive number.")
        return price


# Registration Form with enforced university email validation
class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        help_text="Use your university email (@student.gla.ac.uk)."
    )

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]

    def clean_email(self):
        """Ensure only university emails can be used for registration."""
        email = self.cleaned_data.get("email")
        if not re.match(r"^\d{7}[A-Z]@student\.gla\.ac\.uk$", email):
            raise forms.ValidationError("Invalid email. Use a valid university email (@student.gla.ac.uk).")
        return email

# Report Form for reporting inappropriate listings or defective items
class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reported_item', 'reason', 'description', 'status']
        labels = {
            'reason': 'Reason for Reporting',
            'description': 'Additional Details (Optional)',
        }
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_description(self):
        """Ensure the report description is not excessively short or offensive."""
        description = self.cleaned_data.get("description")
        if description and len(description) < 10:
            raise forms.ValidationError("Please provide more details (at least 10 characters).")
        if any(word in description.lower() for word in ["spam", "fake", "test"]):
            raise forms.ValidationError("Inappropriate words detected in the description.")
        return description

class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['price']

class UserRatingForm(forms.ModelForm):
    class Meta:
        model = UserRating
        fields = ['rating', 'comment']

class CustomUserForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'profile_image', 'bio']