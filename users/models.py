from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from phonenumber_field.modelfields import PhoneNumberField

from django.db import models


class CustomUserManager(BaseUserManager):
    """Кастомный менеджер для создания пользователей"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)

    def make_random_password(self, length=10):
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits,
                                      k=length))


class User(AbstractBaseUser, PermissionsMixin):
    """Полностью своя модель пользователя"""

    email = models.EmailField(unique=True)
    vk_id = models.CharField(max_length=25, blank=True, null=True)
    is_washer = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class VkUser(models.Model):
    """Модель для связи vk-пользователя с Django User."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='vk_profile'
    )
    vk_id = models.BigIntegerField(
        'vk ID',
        unique=True,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    phone_number = PhoneNumberField(
        'Телефон',
        region='RU',
        error_messages={
            'invalid': 'Введите корректный номер телефона в формате +79991234567',
            'max_length': 'Номер телефона слишком длинный',
            'min_length': 'Номер телефона слишком короткий',
        },
        blank=True, null=True
    )

    def __str__(self):
        return self.vk_id
