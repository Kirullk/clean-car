from datetime import datetime, timedelta

from django.db.models import Count, Q
from django.utils import timezone

from .models import Appointment, Washer, WorkingHours, WasherSchedule
from .business_constants import BREAKTIME


def get_start_end_time(date):
    day_of_week = date.weekday()
    try:
        working_hours = WorkingHours.objects.get(day=day_of_week,
                                                 is_working=True)
    except WorkingHours.DoesNotExist:
        return []
    return (timezone.make_aware(
        datetime.combine(date, working_hours.open_time)
        ),
            timezone.make_aware(
        datetime.combine(date, working_hours.close_time)
        ))


def is_working_day(washer, date):
    """Проверяет, работает ли мойщик в указанную дату."""
    try:
        schedule = WasherSchedule.objects.get(washer=washer, date=date)
        return schedule.is_working
    except WasherSchedule.DoesNotExist:
        # Если нет записи — считаем, что не работает.
        return False


def make_washer(service, current, duration):
    washers = Washer.objects.filter(
        category__in=service.washer_category.all(),
        is_active=True
    )
    if not washers:
        return None
    # Проверка, работает ли мойщик в нужный день.
    available_washers = []
    for washer in washers:
        if is_working_day(washer, current.date()):
            available_washers.append(washer)

    if not available_washers:
        return None

    week_ago = datetime.today() - timedelta(days=7)
    washers_with_count = Washer.objects.filter(
        id__in=[w.id for w in available_washers]
    ).annotate(
        appointments_count=Count(
            'appointments',
            filter=Q(appointments__date__gte=week_ago)
        )
    )
    for washer in washers_with_count.order_by('appointments_count'):
        for app in washer.appointments.filter(date__date=current.date()):
            end = app.date + timedelta(
                hours=app.service.average_time.hour,
                minutes=app.service.average_time.minute
            )
            if app.date < current + duration and current < end:
                break
        else:
            return washer
    return None


def left_only_fresh_slots(date, slots):
    if date == timezone.now().date():
        now = timezone.now()
        return [(slot, washer) for slot, washer in slots if slot > now]
    return slots


def get_free_slots(service, date, box):
    # Получаем все записи на определенную дату и бокс.
    all_appointments = Appointment.objects.filter(date__date=date,
                                                  box=box).order_by('date')

    # Получим время, начала и конца формирования слотов.
    working_hours = get_start_end_time(date)
    if not working_hours:
        return []
    start, end = working_hours
    # Получаем время выполнения выбранной услуги.
    service_duration = timedelta(
        hours=service.average_time.hour,
        minutes=service.average_time.minute,
    )
    # Устанавливем переменную, которой будем ходить вперед.
    current = start
    # Далее начинается перебор записей.
    slots = []
    for appointment in all_appointments:
        while current + service_duration + BREAKTIME <= appointment.date:
            washer = make_washer(service, current, service_duration)
            if washer:
                slots.append((current, washer))
                current = current + service_duration
            else:
                # Если мойщиков нет, ждем 15 минут,
                # может кто-то освободиться.
                current += timedelta(minutes=15)
        # Если мы дошли до записи, которая пересекается
        # с нужным слотом, мы ее обходим.
        current = appointment.date + timedelta(hours=appointment.service.average_time.hour,
                                               minutes=appointment.service.average_time.minute)
    # Как только все записи перебрали,
    # до окончания работы автомойки заполняем список слотами.
    while current + service_duration <= end:
        washer = make_washer(service, current, service_duration)
        if washer:
            slots.append((current, washer))
            current = current + service_duration
        else:
            # Если мойщиков нет, ждем 15 минут,
            # может кто-то освободиться.
            current += timedelta(minutes=15)
    # Отсекаем завершившиеся записи.
    slots = left_only_fresh_slots(date, slots)
    return slots
