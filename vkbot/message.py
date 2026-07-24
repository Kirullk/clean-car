import datetime

from django.utils import timezone

from users.models import VkUser
from .utils import get_services
from .handlers import get_or_create_state
from wash.models import WorkingHours, Service, Washer


def message_greetings():
    now = timezone.localtime(timezone.now())
    day_of_week = now.weekday()
    current_time = now.time()
    try:
        working_hours = WorkingHours.objects.get(day=day_of_week,
                                                 is_working=True)
        open_time = working_hours.open_time
        close_time = working_hours.close_time

        # Проверяем, открыто ли сейчас
        if open_time <= current_time <= close_time:
            status = f"🟢 Мы открыты! Записывайтесь прямо сейчас. Сегодня мы работаем до {close_time.strftime('%H:%M')}"
        else:
            status = f"🟡 Сегодня мы работаем с {open_time.strftime('%H:%M')} до {close_time.strftime('%H:%M')}. Сейчас мы закрыты, но вы можете записаться."

        return (
            "🚗 Добро пожаловать в автомойку «Clean Car»!\n\n"
            f"{status}\n\n"
            "📅 Вы можете записаться на удобное для вас время.\n"
            "📋 Посмотреть свои записи — нажмите «Мои записи».\n"
            "🔧 Записаться — нажмите «Записаться»."
        )

    except WorkingHours.DoesNotExist:
        return (
            "🚗 Добро пожаловать в автомойку «Clean Car»!\n\n"
            "🔴 Сегодня мы не работаем.\n"
            "📅 Но вы можете записаться на другие дни.\n\n"
            "🔧 Нажмите «Записаться», чтобы выбрать услугу и удобное время."
        )


def message_services():
    services = get_services()
    if not services:
        return None
    text = "🔧 Выберите услугу:\n\n"
    for idx, service in enumerate(services, 1):
        text += f"{idx}. {service['name']} — {service['price']} ₽\n"
        text += f"   ⏱ {service['average_time']}\n\n"
    return text


def message_slot(service_id, date=None, box=None):
    if box:
        return "Бокс выбран."
    if date:
        return "Дата выбрана."
    service = Service.objects.get(id=service_id)

    text = (
        f"🔧 {service.name}\n\n"
        f"📝 {service.description}\n\n"
        f"⏱ Длительность: {service.average_time.strftime('%H:%M')}\n"
        f"💰 Стоимость: {service.price} ₽\n\n"
        f"📅 Выберите дату и время для записи."
    )
    return text


def message_confirm(user_id):
    state = get_or_create_state(user_id)
    vk_user = VkUser.objects.get(vk_id=user_id)

    service_id = state.service_id
    time = state.time
    box = state.box
    date = state.date
    washer_id = state.washer_id

    phone = vk_user.phone_number

    service = Service.objects.get(id=service_id)
    service_name = service.name

    washer = Washer.objects.get(id=washer_id)
    washer_name = washer.name

    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        date_formatted = date_obj.strftime('%d.%m.%Y')
    except:
        date_formatted = date

    text = (
        "🔍 Проверьте данные записи:\n\n"
        f"📌 Услуга: {service_name}\n"
        f"📅 Дата: {date_formatted}\n"
        f"⏰ Время: {time}\n"
        f"🚗 Бокс: {box}\n"
        f"🧑‍🔧 Мойщик: {washer_name}\n"
        f"📱 Телефон: {phone}\n\n"
        "✅ Всё верно? Нажмите «Подтвердить»"
    )

    return text


def message_success(user_id):
    state = get_or_create_state(user_id)

    # Получаем данные из состояния
    service_id = state.service_id
    time = state.time
    box = state.box
    date = state.date
    washer_id = state.washer_id

    # Получаем названия по ID
    print(service_id)
    service = Service.objects.get(id=service_id)
    washer = Washer.objects.get(id=washer_id)

    # Форматируем дату
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        date_formatted = date_obj.strftime('%d.%m.%Y')
    except:
        date_formatted = date

    text = (
        "✅ Запись успешно создана!\n\n"
        f"📌 Услуга: {service.name}\n"
        f"📅 Дата: {date_formatted}\n"
        f"⏰ Время: {time}\n"
        f"🚗 Бокс: {box}\n"
        f"🧑‍🔧 Мойщик: {washer.name}\n\n"
        "📋 Посмотреть записи — «Мои записи»\n"
    )

    return text
