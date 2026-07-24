import os
import re
import json
import random

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api import VkApi
from dotenv import load_dotenv

from .handlers import (handle_appointments, handle_confirm, handle_create,
                       handle_services, handle_slots, handle_menu,
                       handle_confirm_phone, handle_phone_input)


load_dotenv()

VK_TOKEN = os.getenv('VK_TOKEN')
GROUP_ID = os.getenv('GROUP_ID')
PAYLOADS = {
    'menu': handle_menu,
    'my_appointments': handle_appointments,
    'services': handle_services,
    'slots': handle_slots,
    'confirm_phone': handle_confirm_phone,
    'confirm': handle_confirm,
    'create_appointment': handle_create
}


def main():
    vk_session = VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            message = event.object.message
            text = message.get('text', '').strip().lower()
            payload = message.get('payload')
            if payload:
                payload = json.loads(payload)
                handler = PAYLOADS.get(payload.get('type'))
                if handler:
                    handler(vk, message)
                    continue

            if text.lower() == 'начать':
                handle_menu(vk, message)
            elif text.lower() == 'записаться':
                handle_services(vk, message)
            elif text.lower() == 'мои записи':
                handle_appointments(vk, message)
            elif re.match(r'^\+?[0-9]{10,15}$', text):
                handle_phone_input(vk, message)
            else:
                vk.messages.send(
                    user_id=message['from_id'],
                    message="Я вас не понял. Напишите 'Начать' или нажмите кнопку.",
                    random_id=random.randint(0, 100000)
                )


if __name__ == '__main__':
    main()
