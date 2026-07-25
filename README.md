# Clean Car API

API для сервиса бронирования автомойки. Проект позволяет записываться на мойку, выбирать услуги, боксы, мойщиков, просматривать свои записи и управлять бронированием через веб-интерфейс и VK-бота.

---

## Проект работает на сервере по ссылке https://milojop.pythonanywhere.com/.

## Использованный технологический стек

- **Python 3.12** — язык программирования
- **Django 4.2** — веб-фреймворк
- **Django REST Framework 3.15** — создание API
- **ORM Django** — взаимодействие с базой данных
- **Simple JWT** — аутентификация через JWT-токены
- **SQLite** — база данных (по умолчанию)
- **Djoser** — управление пользователями и аутентификация
- **VK API** — интеграция с VK-ботом
- **vk_api** — работа с ботом

---

## Как запустить проект

### 1. Клонировать репозиторий.

```bash
git clone https://github.com/Kirullk/clean-car.git

### 2. Создать и активировать виртуальное окружение.

```bash
python3 -m venv venv
source venv/bin/activate  # для Linux/macOS
# venv\Scripts\activate  # для Windows

### 3. Установить зависимости.

```bash
pip install -r requirements.txt

### 5. Выполнить миграции базы данных.

```bash
python manage.py migrate







