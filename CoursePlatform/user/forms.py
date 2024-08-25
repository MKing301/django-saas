from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms


class CustomUserCreationForm(UserCreationForm):
    usable_password = None
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')