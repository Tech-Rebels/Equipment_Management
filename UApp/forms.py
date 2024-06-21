from django import forms
from .models import Equipment, Student
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class CreateUserForm(UserCreationForm):
    email = forms.EmailInput()
    
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

class UserEditForm(UserChangeForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'password')

class AddEquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'count', 'category']

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'count', 'category']

