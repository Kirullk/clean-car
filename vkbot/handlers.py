import random
import json
import re

from django.utils import timezone

from users.models import VkUser
from .keyboards import keyboard_menu, keyboard_to_menu, keyboard_services, keyboard_slots, keyboard_confirm, keyboard_send_number
from .utils import create_vk_user, get_slots, post_appointment, get_or_create_state, clear_state
from .message import message_greetings, message_services, message_slot, message_confirm, message_success


def handle_menu(vk, message):
    user_id = message['from_id']
    try:
        VkUser.objects.get(vk_id=user_id)
        return vk.messages.send(
            user_id=user_id,
            message=message_greetings(),
            keyboard=keyboard_menu,
            random_id=random.randint(0, 100000)
        )
    except VkUser.DoesNotExist:
        create_vk_user(user_id)
        return vk.messages.send(
            user_id=user_id,
            message=message_greetings(),
            keyboard=keyboard_menu,
            random_id=random.randint(0, 100000)
        )


def handle_appointments(vk, message):
    user_id = message['from_id']
    appointments = VkUser.objects.get(vk_id=user_id).user.appointments.all().order_by('-date')

    if not appointments:
        return vk.messages.send(
            user_id=user_id,
            message="📭 У вас пока нет записей.",
            keyboard=keyboard_to_menu,
            random_id=random.randint(0, 100000)
        )

    text = "📋 Ваши записи\n\n"
    for idx, app in enumerate(appointments[:10], 1):
        # ✅ Преобразуем время в локальное
        local_time = timezone.localtime(app.date)
        
        text += (
            f"{idx}. {app.service.name}\n"
            f"   📅 {local_time.strftime('%d.%m.%Y')} в {local_time.strftime('%H:%M')}\n"
            f"   🚗 Бокс: {app.box.number} | 🧑‍🔧 Мойщик: {app.washer.name}\n"
            f"   📞 {app.client_name} | {app.phone_number}\n\n"
        )

    if appointments.count() > 10:
        text += f"...и ещё {appointments.count() - 10} записей"

    return vk.messages.send(
        user_id=user_id,
        message=text,
        keyboard=keyboard_to_menu,
        random_id=random.randint(0, 100000)
    )


def handle_services(vk, message):
    user_id = message['from_id']

    clear_state(user_id)

    message_to_user = message_services()
    if message_to_user:
        return vk.messages.send(
            user_id=user_id,
            message=message_to_user,
            keyboard=keyboard_services(),
            random_id=random.randint(0, 100000)
        )
    return vk.messages.send(
        user_id=user_id,
        message="😕 Услуги временно недоступны",
        keyboard=keyboard_to_menu,
        random_id=random.randint(0, 100000)
    )


def handle_slots(vk, message):
    user_id = message['from_id']
    data = json.loads(message.get('payload'))
    box = data.get('box')
    date = data.get('date')
    state = get_or_create_state(user_id)

    state.service_id = data.get('service_id')
    state.save()

    slots = get_slots(state.service_id, box=box, date=date)
    if not slots.get('available_slots'):
        return vk.messages.send(
            user_id=user_id,
            message='Нет свободного времени.',
            keyboard=keyboard_slots(slots),
            random_id=random.randint(0, 100000)
        )
    message_to_user = message_slot(state.service_id,
                                   box=box,
                                   date=date)
    return vk.messages.send(
        user_id=user_id,
        message=message_to_user,
        keyboard=keyboard_slots(slots),
        random_id=random.randint(0, 100000)
    )


def handle_confirm_phone(vk, message):
    user_id = message['from_id']
    data = json.loads(message.get('payload'))
    state = get_or_create_state(user_id)

    state.washer_id = data.get('washer_id')
    state.time = data.get('time')
    state.date = data.get('date')
    state.box = data.get('box')
    state.save()
    text = 'Напишите номер, чтобы мы напомнили вам за час до мойки.'
    return vk.messages.send(
        user_id=user_id,
        message=text,
        keyboard=keyboard_send_number(user_id),
        random_id=random.randint(0, 100000)
    )


def handle_phone_input(vk, message):
    user_id = message['from_id']
    phone = message['text'].strip()

    if not re.match(r'^\+?[0-9]{10,15}$', phone):
        return vk.messages.send(
            user_id=user_id,
            message="❌ Некорректный номер. Введите в формате +79991234567",
            keyboard=keyboard_send_number(user_id),
            random_id=random.randint(0, 100000)
        )

    vk_user = VkUser.objects.get(vk_id=user_id)
    vk_user.phone_number = phone
    vk_user.save()
    handle_confirm(vk, message)


def handle_confirm(vk, message):
    user_id = message['from_id']
    return vk.messages.send(
        user_id=user_id,
        message=message_confirm(user_id),
        keyboard=keyboard_confirm(user_id),
        random_id=random.randint(0, 100000)
    )


def handle_create(vk, message):
    user_id = message['from_id']
    user_info = vk.users.get(user_ids=user_id)[0]
    first_name = user_info['first_name']

    result = post_appointment(user_id, first_name)

    if result.get('error'):
        return vk.messages.send(
            user_id=user_id,
            message=f"❌ Ошибка: {result.get('error')}",
            random_id=random.randint(0, 100000)
        )

    return vk.messages.send(
        user_id=user_id,
        message=message_success(user_id),
        keyboard=keyboard_menu,
        random_id=random.randint(0, 100000)
    )
