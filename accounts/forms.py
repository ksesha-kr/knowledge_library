from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import RegistrationKey

User = get_user_model()

class CustomRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )

    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('teacher', 'Преподаватель'),
        ('admin', 'Администратор'),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Роль'
    )

    registration_key = forms.CharField(
        max_length=64,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ключ регистрации'
        }),
        label='Ключ регистрации'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role', 'registration_key')

    def clean_registration_key(self):
        from django.utils import timezone

        key_value = self.cleaned_data.get('registration_key', '').strip()
        role = self.cleaned_data.get('role')

        if not key_value:
            raise forms.ValidationError("Требуется ключ регистрации")

        try:
            key = RegistrationKey.objects.get(key=key_value, is_active=True)

            if key.role != role:
                raise forms.ValidationError(
                    f"Этот ключ предназначен для роли '{key.get_role_display()}', а вы выбрали '{dict(self.ROLE_CHOICES)[role]}'"
                )

            if key.expires_at and timezone.now() > key.expires_at:
                raise forms.ValidationError("Срок действия ключа истек")

            if key.max_uses > 0 and key.uses >= key.max_uses:
                raise forms.ValidationError("Ключ уже использован максимальное число раз")

            self.cleaned_data['registration_key_obj'] = key

            return key_value

        except RegistrationKey.DoesNotExist:
            raise forms.ValidationError("Неверный ключ регистрации или ключ неактивен")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

            role = self.cleaned_data['role']
            if role == 'admin':
                user.is_superuser = True
                user.is_staff = True
            elif role == 'teacher':
                user.is_staff = True

            user.save()

            registration_key = self.cleaned_data.get('registration_key_obj')
            if registration_key:
                registration_key.uses += 1
                registration_key.save()

        return user
class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Имя пользователя'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})