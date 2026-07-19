from django.db import models
from django.contrib.auth import get_user_model
from phonenumber_field.modelfields import PhoneNumberField


User = get_user_model()


class Box(models.Model):
    class StatusChoices(models.TextChoices):
        WORKING = 'working', 'Работает'
        NOT_WORKING = 'not_working', 'Не работает'

    number = models.CharField(
        'Номер бокса',
        max_length=10,
        primary_key=True
    )
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.WORKING
    )
    max_height = models.DecimalField(
        'Максимальная высота (м)',
        max_digits=5,
        decimal_places=2
    )

    class Meta:
        verbose_name = 'Бокс'
        verbose_name_plural = 'Боксы'
        ordering = ('number',)

    def __str__(self):
        return f'Бокс {self.number}'


class WasherCategory(models.Model):
    class StatusChoices(models.TextChoices):
        INTERN = 'intern', 'Стажёр'
        SPECIALIST = 'specialist', 'Специалист'
        SENIOR = 'senior', 'Старший специалист'

    name = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        unique=True
    )

    class Meta:
        verbose_name = 'Категория мойщика'
        verbose_name_plural = 'Категории мойщиков'

    def __str__(self):
        return self.get_name_display()


class Service(models.Model):
    name = models.CharField(
        'Название услуги',
        max_length=100
    )
    description = models.TextField(
        'Описание',
        blank=True
    )
    is_active = models.BooleanField(
        'Активна',
        default=True
    )
    average_time = models.TimeField(
        'Среднее время выполнения',
        help_text='Формат: ЧЧ:ММ'
    )
    boxes = models.ManyToManyField(
        Box,
        verbose_name='Боксы',
        related_name='services'
    )
    price = models.DecimalField(
        'Стоимость',
        max_digits=10,
        decimal_places=2
    )
    washer_category = models.ManyToManyField(
        WasherCategory,
        verbose_name='Категория мойщика',
        related_name='services'
    )
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} - {self.price} руб.'


class WorkingHours(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ]

    day = models.IntegerField('День недели', choices=DAYS_OF_WEEK, unique=True)
    open_time = models.TimeField('Время открытия')
    close_time = models.TimeField('Время закрытия')
    is_working = models.BooleanField('Рабочий день', default=True)

    class Meta:
        verbose_name = 'День недели'
        verbose_name_plural = 'Дни недели'

    def __str__(self):
        return self.get_day_display()


class ShiftType(models.Model):
    class ShiftChoices(models.TextChoices):
        TWO_TWO = '2_2', '2/2'
        FIVE_TWO = '5_2', '5/2'
        THREE_THREE = '3_3', '3/3'
        SIX_ONE = '6_1', '6/1'

    name = models.CharField(
        'Название графика',
        max_length=20,
        choices=ShiftChoices.choices,
        unique=True
    )

    class Meta:
        verbose_name = 'Вид смены'
        verbose_name_plural = 'Виды смен'

    def __str__(self):
        return self.get_name_display()


class Washer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='washer_profile'
    )
    name = models.CharField(
        'Имя мойщика',
        max_length=100
    )
    is_active = models.BooleanField(
        'Активен',
        default=True
    )
    category = models.ForeignKey(
        WasherCategory,
        on_delete=models.CASCADE,
        verbose_name='Категория',
        related_name='washers'
    )
    hire_date = models.DateField(
        'Дата приема',
        auto_now_add=True
    )
    phone = PhoneNumberField(
        'Телефон',
        region='RU',
        error_messages={
            'invalid': 'Введите корректный номер телефона в формате +79991234567',
            'max_length': 'Номер телефона слишком длинный',
            'min_length': 'Номер телефона слишком короткий',
        }
    )
    shift_type = models.ForeignKey(
        ShiftType,
        on_delete=models.PROTECT,
        verbose_name='Тип смены',
        related_name='washers'
    )

    class Meta:
        verbose_name = 'Мойщик'
        verbose_name_plural = 'Мойщики'

    def __str__(self):
        return self.name


class Appointment(models.Model):

    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Клиент',
        related_name='appointments',
        null=True,
        blank=True
    )
    client_name = models.CharField(
        'Имя клиента',
        max_length=50
    )
    phone_number = PhoneNumberField(
        'Телефон',
        region='RU',
        error_messages={
            'invalid': 'Введите корректный номер телефона в формате +79991234567',
            'max_length': 'Номер телефона слишком длинный',
            'min_length': 'Номер телефона слишком короткий',
        }
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        verbose_name='Услуга',
        related_name='appointments'
    )
    date = models.DateTimeField(
        'Время записи'
    )
    washer = models.ForeignKey(
        Washer,
        on_delete=models.PROTECT,
        verbose_name='Мойщик',
        related_name='appointments'
    )
    box = models.ForeignKey(
        Box,
        on_delete=models.PROTECT,
        verbose_name='Бокс',
        related_name='appointments'
    )
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    comment = models.TextField(
        'Комментарий',
        blank=True
    )

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        unique_together = ('service', 'date', 'box',)

    def __str__(self):
        return f'{self.client_name} — {self.service.name} — {self.date.strftime("%d.%m.%Y %H:%M")}'
