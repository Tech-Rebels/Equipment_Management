from django import forms
from .models import Equipment, Student, MedicalKit, Treatment
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
        fields = ['name', 'count', 'order', 'category']
        
    def clean_name(self):
        name = self.cleaned_data['name']
        lab = self.instance.lab if self.instance.pk else self.initial.get('lab')
        if Equipment.objects.filter(lab=lab, name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Equipment name must be unique within the lab (case-insensitive).')
        return name

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'count', 'order', 'category']

class AddMedicalKitForm(forms.ModelForm):
    class Meta:
        model = MedicalKit
        fields = ['kitName', 'equipment', 'order']

class AddTreatmentForm(forms.ModelForm):
    class Meta:
        model = Treatment
        fields = ['treatment', 'order']

class EditTreatmentForm(forms.ModelForm):
    class Meta:
        model = Treatment
        fields = ['treatment', 'order']