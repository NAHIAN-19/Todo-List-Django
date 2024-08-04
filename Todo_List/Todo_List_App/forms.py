from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, SetPasswordForm, UserChangeForm
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth import get_user_model
from Todo_List_App.models import Profile, CustomUser
from django.contrib.auth.models import User
import re

User = get_user_model()  
    
class CustomUserAdminForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = '__all__'
        
class PasswordChangeForm(DjangoPasswordChangeForm):
    def is_empty(self):
        return not (self.cleaned_data.get('old_password') or self.cleaned_data.get('new_password1') or self.cleaned_data.get('new_password2'))
    def clear_errors(self):
        self._errors.clear()
    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if old_password or new_password1 or new_password2:
            if not old_password:
                self.add_error('old_password', 'Please enter your old password.')
            if not new_password1:
                self.add_error('new_password1', 'Please enter your new password.')
            if not new_password2:
                self.add_error('new_password2', 'Please confirm your new password.')

            if new_password1 and new_password2:
                if new_password1 != new_password2:
                    self.add_error('new_password2', 'The two password fields didn’t match.')

                if len(new_password1) < 8:
                    self.add_error('new_password1', 'The new password must be at least 8 characters long.')

                if not re.search(r'\d', new_password1):
                    self.add_error('new_password1', 'The new password must contain at least one number.')

                if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password1):
                    self.add_error('new_password1', 'The new password must contain at least one special character.')

                if old_password and new_password1 == old_password:
                    self.add_error('new_password1', 'The new password cannot be the same as the old password.')

        return cleaned_data

class SignInForm(AuthenticationForm):
    pass

class SignUpForm(UserCreationForm):
    email = forms.EmailField()
    firstName = forms.CharField(max_length=30, required=False, initial='Name1')
    lastName = forms.CharField(max_length=30, required=False, initial='Name2')
    phone = forms.CharField(max_length=15, required=False, initial='0123456789')
    address = forms.CharField(max_length=180, required=False, initial='Earth')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'firstName', 'lastName', 'phone', 'address']

    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already in use. Please choose a different one.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already associated with an account.')
        return email


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'autocomplete': 'off'}))
    firstName = forms.CharField(max_length=30, required=False, label="First Name")
    lastName = forms.CharField(max_length=30, required=False, label="Last Name")
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(max_length=180, required=False)
    bio = forms.CharField(max_length=230, required=False, widget=forms.Textarea)
    gender = forms.ChoiceField(choices=Profile.GENDER_CHOICES, required=False)
    enableEmailNotifications = forms.BooleanField(required=False)

    class Meta:
        model = Profile
        fields = ['profilePicture', 'bio', 'gender', 'enableEmailNotifications']

    def clean_email(self):
        email = self.cleaned_data['email']
        user = self.instance.user

        if User.objects.exclude(pk=user.pk).filter(email=email).exists():
            raise forms.ValidationError('This email address is already associated with an account.')

        return email
    
    def __init__(self, *args, **kwargs):
        user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)
        if user_instance:
            # Initialize fields with user instance data
            self.fields['firstName'].initial = user_instance.firstName
            self.fields['lastName'].initial = user_instance.lastName
            self.fields['email'].initial = user_instance.email
            self.fields['phone'].initial = user_instance.phone
            self.fields['address'].initial = user_instance.address
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.firstName = self.cleaned_data['firstName']
        user.lastName = self.cleaned_data['lastName']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        if commit:
            user.save()
            profile.save()
        return profile
    
    
class CustomSetPasswordForm(SetPasswordForm):
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 or new_password2:
            if not new_password1:
                self.add_error('new_password1', 'Please enter your new password.')
            if not new_password2:
                self.add_error('new_password2', 'Please confirm your new password.')

            if new_password1 and new_password2:
                if new_password1 != new_password2:
                    self.add_error('new_password2', 'The two password fields didn’t match.')

                if len(new_password1) < 8:
                    self.add_error('new_password1', 'The new password must be at least 8 characters long.')

                if not re.search(r'\d', new_password1):
                    self.add_error('new_password1', 'The new password must contain at least one number.')

                if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password1):
                    self.add_error('new_password1', 'The new password must contain at least one special character.')

        return cleaned_data
    