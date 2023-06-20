from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import Profile

class SignInForm(AuthenticationForm):
    pass

class SignUpForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ProfileForm(forms.ModelForm):
    email = forms.EmailField()  # Add the email field

    class Meta:
        model = Profile
        fields = ['email', 'profile_picture']  # Include the email field and profile_picture field

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['email'].initial = self.instance.user.email  # Set the initial value of the email field

    def save(self, commit=True):
        self.instance.user.email = self.cleaned_data['email']  # Update the email value in the User model
        return super(ProfileForm, self).save(commit=commit)
