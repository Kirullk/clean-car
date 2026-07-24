import requests

from django.contrib.auth import get_user_model

from users.models import VkUser
from .models import VkUserState


User = get_user_model()
API_URL = 'http://127.0.0.1:8000/api/v1'

BOT_TOKEN = None


def get_or_create_state(user_id):
    """Получает или создаёт состояние для пользователя."""
    vk_user = VkUser.objects.get(vk_id=user_id)
    state, created = VkUserState.objects.get_or_create(user=vk_user)
    return state


def clear_state(user_id):
    """Очищает состояние пользователя."""
    vk_user = VkUser.objects.get(vk_id=user_id)
    VkUserState.objects.filter(user=vk_user).delete()


def create_vk_user(user_id, first_name):
    """Создаёт ВК-пользователя и связанного Django-пользователя."""
    vk_user, created = VkUser.objects.get_or_create(
        vk_id=user_id,
        defaults={
            'client_name': first_name
        }
    )

    if created:
        user = User.objects.create_user(
            username=f'vk_{user_id}',
            email=f'vk_{user_id}@bot.local',
            password='bot_password_123'
        )
        vk_user.user = user
        vk_user.save()

    return vk_user


def get_bot_token():
    """Получает или обновляет JWT-токен для бота."""
    global BOT_TOKEN

    if BOT_TOKEN:
        return BOT_TOKEN

    url = f'{API_URL}/auth/jwt/create/'
    response = requests.post(url, json={
        'email': 'bot@clean-car.ru',  # ← фиксированный email бота!
        'password': 'bot_password_123'  # ← фиксированный пароль!
    })

    if response.status_code == 200:
        BOT_TOKEN = response.json()['access']
        return BOT_TOKEN
    print(f"Ошибка получения токена: {response.status_code} - {response.text}")
    return None


def get_services():
    response = requests.get(f'{API_URL}/services/')
    return response.json() if response.status_code == 200 else []


def get_boxes():
    response = requests.get(f'{API_URL}/boxes/')
    return response.json() if response.status_code == 200 else []


def get_slots(service_id, box=None, date=None):
    url = f'{API_URL}/services/{service_id}/slots/'
    params = []

    if date:
        params.append(f'date={date}')
    if box:
        params.append(f'box={box}')

    if params:
        url += '?' + '&'.join(params)

    response = requests.get(url)
    return response.json() if response.status_code == 200 else None


def post_appointment(user_id, client_name):
    """Создаёт запись через API, беря данные из состояния."""
    try:
        vk_user = VkUser.objects.get(vk_id=user_id)
        state = get_or_create_state(user_id)

        token = get_bot_token()
        if not token:
            return {'error': 'Не удалось получить токен'}

        # Берём данные из состояния
        service_id = state.service_id
        washer_id = state.washer_id
        box = state.box
        date_str = state.date
        time_str = state.time

        if not all([service_id, washer_id, box, date_str, time_str]):
            return {'error': f'Не все данные для записи заполнены: {[service_id, washer_id, box, date_str, time_str]}'}

        datetime_str = f'{date_str}T{time_str}:00'

        appointment = {
            "service": service_id,
            "client": vk_user.user.id,
            "client_name": client_name,
            "phone_number": str(vk_user.phone_number),
            "date": datetime_str,
            "washer": washer_id,
            "box": box
        }

        url = f'{API_URL}/appointments/'
        response = requests.post(
            url,
            json=appointment,
            headers={
                'Authorization': f'Bearer {token}'
            }
        )

        if response.status_code == 201:
            return response.json()
        else:
            return {'error': f'Ошибка API: {response.status_code}',
                    'detail': response.text}

    except VkUser.DoesNotExist:
        return {'error': 'Пользователь не найден'}
    except Exception as e:
        return {'error': str(e)}
