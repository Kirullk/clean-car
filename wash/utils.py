from datetime import datetime, timedelta

from django.db.models import Count, Q
from django.utils import timezone

from .models import Appointment, Washer, WorkingHours
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


def make_washer(service, current, duration):
    washers = Washer.objects.filter(
        category__in=service.washer_category.all(),
        is_active=True
    )
    if not washers:
        return None

    week_ago = datetime.today() - timedelta(days=7)
    washers = washers.annotate(
        appointments_count=Count(
            'appointments',
            filter=Q(appointments__date__gte=week_ago)
        )
    )
    for washer in washers.order_by('appointments_count'):
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
        return [slot for slot in slots if slot > now]
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
        while current + service_duration <= appointment.date:
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
        print(washer, current, service_duration)
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












def generate_slots(service, date):
    # Получаем мойщика, у которого наименьшее количество записей
    # за последние 7 дней.
    washer = choice_washer(service)
    # Получаем все записи мойщика на определенное число.
    all_appointments = washer.appointments.filter(date__date=date)
    print(all_appointments)

    day_of_week = date.weekday()
    try:
        wh = WorkingHours.objects.get(day=day_of_week, is_working=True)
    except WorkingHours.DoesNotExist:
        return []

    open_time = timezone.make_aware(datetime.combine(date, wh.open_time))
    close_time = timezone.make_aware(datetime.combine(date, wh.close_time))
    break_duration = timedelta(minutes=BREAKTIME)

    service_time = service.average_time
    service_duration = timedelta(
        hours=service_time.hour,
        minutes=service_time.minute,
        seconds=service_time.second
    )

    appointments = sorted(all_appointments, key=lambda a: a.date)
    slots = []
    current = open_time

    for app in appointments:
        app_start = app.date
        app_end = app.service.average_time
        app_end = timedelta(
            hours=app_end.hour,
            minutes=app_end.minute,
            seconds=app_end.second
        )
        app_end = app_start + app_end + break_duration

        while current + service_duration + break_duration <= app_start:
            slots.append(current)
            current += service_duration + break_duration

        if current < app_end:
            current = app_end

    while current + service_duration + break_duration <= close_time:
        slots.append(current)
        current += service_duration + break_duration

    slots = left_only_fresh_slots(date, slots)

    return slots, washer
