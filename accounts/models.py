from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import models
from django.contrib.auth.models import User
import secrets
import string
from django.utils import timezone
from datetime import timedelta

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('teacher', 'Преподаватель'),
        ('admin', 'Администратор'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student',
        verbose_name='Роль'
    )
    registration_key = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Ключ регистрации'
    )

    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class RegistrationKey(models.Model):
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('teacher', 'Преподаватель'),
        ('admin', 'Администратор'),
    ]

    key = models.CharField(max_length=64, unique=True, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_registration_keys'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.IntegerField(default=1)
    uses = models.IntegerField(default=0)
    note = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def generate_key(self, length=32):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.key[:12]}... ({self.role})"

    def is_valid(self):
        if not self.is_active:
            return False, "Ключ неактивен"

        if self.max_uses > 0 and self.uses >= self.max_uses:
            return False, "Ключ использован максимальное число раз"

        if self.expires_at and timezone.now() > self.expires_at:
            return False, "Срок действия ключа истек"

        return True, "Ключ действителен"

    def use_key(self):
        if self.is_valid()[0]:
            self.uses += 1
            self.save()
            return True
        return False

    class Meta:
        verbose_name = 'Ключ регистрации'
        verbose_name_plural = 'Ключи регистрации'