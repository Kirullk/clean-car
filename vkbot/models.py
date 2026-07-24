from django.db import models

from users.models import VkUser


class VkUserState(models.Model):
    """Состояние пользователя VK для хранения данных бронирования."""

    user = models.OneToOneField(
        VkUser,
        on_delete=models.CASCADE,
        related_name='state',
        verbose_name='Пользователь VK'
    )
    service_id = models.IntegerField(
        'ID услуги',
        null=True,
        blank=True
    )
    time = models.CharField(
        'Время',
        max_length=10,
        blank=True,
        help_text='Формат: ЧЧ:ММ'
    )
    box = models.CharField(
        'Бокс',
        max_length=10,
        blank=True
    )
    date = models.DateField(
        'Дата',
        null=True,
        blank=True
    )
    washer_id = models.IntegerField(
        'ID мойщика',
        null=True,
        blank=True
    )
    client_name = models.CharField(
        'Имя клиента',
        max_length=100,
        blank=True
    )
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Состояние пользователя VK'
        verbose_name_plural = 'Состояния пользователей VK'
        ordering = ('-updated_at',)

    def __str__(self):
        return f'{self.user} — состояние от {self.updated_at.strftime("%d.%m.%Y %H:%M")}'

    def clear(self):
        """Очищает состояние пользователя после завершения бронирования."""
        self.service_id = None
        self.time = ''
        self.box = ''
        self.date = None
        self.washer_id = None
        self.client_name = ''
        self.save()
