"""Настройки для запуска тестов: быстрая БД SQLite в памяти, без внешних сервисов."""
from core.settings.base import *  # noqa

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Ускоряем хеширование паролей в тестах.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Не зависим от скомпилированных переводов / статики при тестах.
LANGUAGE_CODE = 'ru'
