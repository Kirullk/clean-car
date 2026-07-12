from datetime import datetime, timedelta

from django.db.models import Count, Q

from .models import WorkingHours, Washer
from .business_constants import BREAKTIME


def generate_slots(all_appointments, service, date):
    """
    Генерирует доступные временные слоты для записи на услугу.
    :param all_appointments: QuerySet записей на эту дату для выбранного бокса
    :param service: объект Service (содержит average_time)
    :param date: дата (date объект) для которой генерируем слоты
    :return: список времен начала свободных слотов (объекты time)
    """
    day_of_week = date.weekday()
    try:
        wh = WorkingHours.objects.get(day=day_of_week, is_working=True)
    except WorkingHours.DoesNotExist:
        return []

    washer = choice_washer(service)
    open_time = datetime.combine(date, wh.open_time)
    close_time = datetime.combine(date, wh.close_time)
    BREAKTIME = timedelta(minutes=BREAKTIME)

    service_duration = service.average_time

    # Сортируем записи по времени начала
    appointments = sorted(all_appointments, key=lambda a: a.date)

    slots = []
    current = open_time

    for app in appointments:
        app_start = app.date
        # Конец записи с учётом времени на услугу и перерыва после неё
        app_end = app_start + app.service.average_time + BREAKTIME

        # Пока есть место до начала следующей записи - добавляем слоты
        while current + service_duration + BREAKTIME <= app_start:
            slots.append((current, washer))
            current += service_duration + BREAKTIME

        # Если текущий момент перекрывается с записью - сдвигаем за её окончание
        if current < app_end:
            current = app_end

    # После всех записей добавляем слоты до закрытия
    while current + service_duration + BREAKTIME <= close_time:
        slots.append((current, washer))
        current += service_duration + BREAKTIME

    return slots


def choice_washer(service):
    """
    Выбирает мойщика с наименьшим количеством записей за последние 7 дней
    """
    # Получаем всех активных мойщиков нужной категории
    washers = Washer.objects.filter(
        category__in=service.washer_category.all(),
        is_active=True
    )
    if not washers:
        return None

    seven_days_ago = datetime.today() - timedelta(days=7)
    
    # Аннотируем количество записей за последние 7 дней
    washers_with_count = washers.annotate(
        appointments_count=Count(
            'appointments',
            filter=Q(appointments__time__gte=seven_days_ago)
        )
    )

    # Выбираем с минимальным количеством
    return washers_with_count.order_by('appointments_count').first()
