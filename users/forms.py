from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """Форма создания пользователя с email вместо username"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'})
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'placeholder': 'Подтвердите пароль'})
    )

    class Meta:
        model = User
        fields = (
            'email',
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'Пользователь с таким email уже существует'
                )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Форма входа с email вместо username"""

    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'autofocus': True})
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(
                self.request,
                username=email,
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    'Неверный email или пароль',
                    code='invalid_login'
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
