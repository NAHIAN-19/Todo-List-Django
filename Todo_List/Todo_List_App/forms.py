from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, SetPasswordForm, UserChangeForm
from django.contrib.auth import get_user_model
from .models import Profile, CustomUser
from django.contrib.auth.models import User

User = get_user_model()

class CustomUserAdminForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = '__all__'
class SignInForm(AuthenticationForm):
    pass

class SignUpForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    phone = forms.CharField(max_length=15, required=False, help_text='Optional.')
    address = forms.CharField(max_length=100, required=False, help_text='Optional.')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'address', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already in use. Please choose a different one.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already associated with an account.')
        return email

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'autocomplete': 'off'}))
    first_name = forms.CharField(max_length=30, required=False, label="First Name")
    last_name = forms.CharField(max_length=30, required=False, label="Last Name")
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(max_length=100, required=False)

    class Meta:
        model = Profile
        fields = ['email','phone','address', 'profile_picture']
    
    def clean_email(self):
        email = self.cleaned_data['email']
        user = self.instance.user

        if User.objects.exclude(pk=user.pk).filter(email=email).exists():
            raise forms.ValidationError('This email address is already associated with an account.')

        return email

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')

        if first_name and last_name:
            full_name = f"{first_name} {last_name}"
            self.instance.full_name = full_name

        return cleaned_data

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label="New Password", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirm New Password", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 != new_password2:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

class SolveForm(forms.Form):
    username = forms.CharField()
    email = forms.EmailField()
