from django import forms
from .models import CustomUser

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'sign__input'})
    )
    agree = forms.BooleanField(required=True)

    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'password']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name', 'class': 'sign__input'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'sign__input'}),
        }

