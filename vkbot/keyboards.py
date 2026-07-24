import json
from datetime import datetime, timedelta

from django.utils import timezone

from .utils import get_services
from users.models import VkUser
from .utils import get_or_create_state


keyboard_menu = {
    "one_time": False,
    "buttons": [
        [
            {
                "action": {"type": "text", "label": "Мои записи",
                           "payload": json.dumps({"type": "my_appointments"})},
                "color": "primary"
            },
            {
                "action": {"type": "text", "label": "Записаться",
                           "payload": json.dumps({"type": "services"})},
                "color": "positive"
            }
        ]
    ]
}
keyboard_menu = json.dumps(keyboard_menu, ensure_ascii=False)

keyboard_to_menu = {
    "one_time": False,
    "buttons": [
        [
            {
                "action": {"type": "text", "label": "Назад",
                           "payload": json.dumps({"type": "menu"})},
                "color": "secondary"
            },
        ]
    ]
}
keyboard_to_menu = json.dumps(keyboard_to_menu, ensure_ascii=False)

services = get_services()


def keyboard_services():
    buttons = []
    row = []
    for service in services:
        row.append({
            "action": {
                "type": "text",
                "label": service.get('name'),
                "payload": json.dumps({"type": "slots",
                                       "service_id": service.get('id')})
            },
            "color": "primary"
        })
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([
        {
            "action": {"type": "text", "label": "Назад",
                       "payload": json.dumps({"type": "menu"})},
            "color": "secondary"
        }
    ])
    return json.dumps({"one_time": False, "buttons": buttons},
                      ensure_ascii=False)


def keyboard_slots(slots_data):
    buttons = []
    row = []
    max_buttons_in_row = 4
    boxes_row = []

    for box in slots_data.get('boxes', []):
        is_selected = box == slots_data.get('selected_box')
        service = slots_data.get("service")
        boxes_row.append({
            "action": {
                "type": "text",
                "label": f"Бокс {box}",
                "payload": json.dumps({"type": "slots", "box": box,
                                       "service_id": service.get("id"),
                                       "date": datetime.fromisoformat(slots_data.get('selected_date')).strftime('%Y.%d.%m')})
            },
            "color": "positive" if is_selected else "primary"
        })
        if len(boxes_row) >= max_buttons_in_row:
            buttons.append(boxes_row)
            boxes_row = []
        if len(boxes_row) > 1:
            buttons.append(boxes_row)

    dates_row = []
    selected_date_str = slots_data.get('selected_date')
    prev_date, next_date = get_adjacent_dates(selected_date_str)
    service_id = slots_data.get('service', {}).get('id')

    if prev_date:
        dates_row.append({
            "action": {
                "type": "text",
                "label": datetime.strptime(prev_date, '%Y-%m-%d').strftime('%d.%m'),
                "payload": json.dumps({
                    "type": "slots",
                    "date": datetime.strptime(prev_date, '%Y-%m-%d'
                                              ).strftime('%Y.%d.%m'),
                    "service_id": service_id
                })
            },
            "color": "secondary"
        })

    dates_row.append({
        "action": {
            "type": "text",
            "label": datetime.strptime(selected_date_str, '%Y-%m-%d').strftime('%d.%m'),
            "payload": json.dumps({
                "type": "slots",
                "date": datetime.strptime(selected_date_str, '%Y-%m-%d').strftime('%Y.%d.%m'),
                "service_id": service_id
            })
        },
        "color": "positive"
    })

    if next_date:
        dates_row.append({
            "action": {
                "type": "text",
                "label": datetime.strptime(next_date, '%Y-%m-%d').strftime('%d.%m'),
                "payload": json.dumps({
                    "type": "slots",
                    "date": datetime.strptime(next_date, '%Y-%m-%d').strftime('%Y.%d.%m'),
                    "service_id": service_id
                })
            },
            "color": "secondary"
        })

    if dates_row:
        buttons.append(dates_row)

    row = []
    for slot in slots_data.get('available_slots', []):
        row.append({
            "action": {
                "type": "text",
                "label": slot['time'],
                "payload": json.dumps({
                    "type": "confirm_phone",
                    "washer_id": slot['washer_id'],
                    "time": slot['time'],
                    "box": slots_data['selected_box'],
                    "date": slots_data['selected_date']
                })
            },
            "color": "primary"
        })
        if len(row) >= max_buttons_in_row:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    if len(buttons) > 8:
        buttons = buttons[:9]
    buttons.append([{
        "action": {"type": "text", "label": "Назад",
                   "payload": json.dumps({"type": "services"})},
        "color": "secondary"
    }])

    return json.dumps({"one_time": False, "buttons": buttons}, ensure_ascii=False)


def get_adjacent_dates(selected_date_str):
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    today = timezone.now().date()
    last_day = today + timedelta(days=7)

    prev_date = None
    next_date = None

    if selected_date > today:
        prev_date = (selected_date - timedelta(days=1)).isoformat()

    if selected_date < last_day:
        next_date = (selected_date + timedelta(days=1)).isoformat()

    return prev_date, next_date


def keyboard_send_number(user_id):
    vkuser = VkUser.objects.get(vk_id=user_id)
    state = get_or_create_state(user_id)
    buttons = []

    back_button = [{
        "action": {
            "type": "text",
            "label": "🔙 Назад",
            "payload": json.dumps({
                "type": "slots",
                "service_id": state.service_id
            })
        },
        "color": "secondary"
    }]

    if vkuser.phone_number:
        phone_button = [{
            "action": {
                "type": "text",
                "label": f"{vkuser.phone_number}",
                "payload": json.dumps({
                    "type": "confirm"})
            },
            "color": "positive"
        }]
        buttons.append(phone_button)

    buttons.append(back_button)

    keyboard = {
        "one_time": False,
        "buttons": buttons
    }

    return json.dumps(keyboard, ensure_ascii=False)


def keyboard_confirm(user_id):
    state = get_or_create_state(user_id)
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "label": "✅ Подтвердить",
                        "payload": json.dumps({
                            "type": "create_appointment"})
                    },
                    "color": "positive"
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "label": "Назад",
                        "payload": json.dumps({"type": "slots",
                                               "service_id": state.service_id})
                        },
                    "color": "secondary"
                }
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)
