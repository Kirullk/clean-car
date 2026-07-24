from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from .models import Washer, WasherSchedule


def calculate_is_working(shift_name, days_since_hire):
    """Определяет, работает ли мойщик по графику."""
    if shift_name == '2_2':
        return days_since_hire % 4 < 2
    elif shift_name == '5_2':
        return days_since_hire % 7 < 5
    elif shift_name == '3_3':
        return days_since_hire % 6 < 3
    elif shift_name == '6_1':
        return days_since_hire % 7 < 6
    return False


@receiver(post_save, sender=Washer)
def create_washer_schedule(sender, instance, created, **kwargs):
    """При создании мойщика генерируем график на 30 дней."""
    if created:
        start_date = instance.hire_date
        for i in range(30):
            current_date = start_date + timedelta(days=i)
            is_working = calculate_is_working(instance.shift_type.name, i)

            WasherSchedule.objects.create(
                washer=instance,
                date=current_date,
                is_working=is_working
            )
