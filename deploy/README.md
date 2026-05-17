# 🚀 Деплой KIKI Academy на сервер

Полностью автоматизированный деплой через Docker + Nginx + Let's Encrypt SSL.

## Требования

- **Сервер**: Ubuntu/Debian VPS с публичным IP
- **Домен**: поддомен (например `academy.kiki.kg`) с A-записью DNS, указывающей на IP сервера
- **Порты 80 и 443**: должны быть открыты (для HTTP и HTTPS)
- **Email**: для Let's Encrypt уведомлений о сертификате

## Быстрый старт

```bash
# 1. Клонируй репозиторий
git clone https://github.com/Nurbolottop/KIKIACADEMY.git
cd KIKIACADEMY

# 2. Запусти интерактивный скрипт
bash deploy/deploy.sh
```

Скрипт спросит:
- **Домен** (например `academy.kiki.kg`)
- **Email** для Let's Encrypt
- **Тестовый сертификат?** (для тестов используй staging — у LE есть лимит на боевые сертификаты)
- **Телефон, пароль, имя, фамилию** администратора (FOUNDER)

Всё остальное он сделает сам:
- Установит Docker (если нет)
- Сгенерирует `SECRET_KEY` и пароль для PostgreSQL
- Соберёт и запустит контейнеры: **db**, **redis**, **web** (Django+Gunicorn), **nginx**, **certbot**
- Применит миграции, соберёт статику, скомпилирует переводы
- Создаст администратора одной командой
- Получит SSL-сертификат через Let's Encrypt
- Настроит HTTP → HTTPS редирект
- Запустит автоматическое продление сертификата каждые 12 часов

## Структура

```
deploy/
├── docker-compose.prod.yml    # production compose (5 сервисов)
├── Dockerfile.prod            # gunicorn вместо runserver
├── entrypoint.sh              # ждёт БД → миграции → collectstatic → compilemessages → run
├── deploy.sh                  # 👈 главный интерактивный скрипт
├── init-letsencrypt.sh        # получает SSL-сертификат через webroot
├── nginx/
│   ├── templates/
│   │   ├── app-http.conf.template   # этап 1: HTTP-only (для получения сертификата)
│   │   └── app-ssl.conf.template    # этап 2: полный HTTPS (после)
│   └── conf.d/                # сгенерированный конфиг (не в git)
└── certbot/                   # сертификаты (создаётся скриптом)
    ├── conf/
    └── www/
```

## Что делает `deploy.sh` пошагово

1. **Проверка Docker** — устанавливает если не найден
2. **Спрашивает параметры** (или читает из существующего `.env`)
3. **Создаёт `.env`** в корне проекта с автогенерированными секретами
4. **Генерирует Nginx HTTP-конфиг** из шаблона
5. **`docker compose up -d --build`** для db, redis, web, nginx
6. **`migrate` + `collectstatic` + `compilemessages`** — выполняет автоматически в entrypoint
7. **Создаёт FOUNDER** через management-команду `create_founder`
8. **Запрашивает SSL** через certbot (webroot challenge)
9. **Переключает Nginx** на HTTPS-конфиг + reload
10. **Запускает certbot** в фоне для auto-renewal

## Управление после деплоя

```bash
cd deploy

# Статус контейнеров
docker compose -f docker-compose.prod.yml ps

# Логи Django
docker compose -f docker-compose.prod.yml logs -f web

# Перезапустить web после изменений
docker compose -f docker-compose.prod.yml restart web

# Зайти в shell контейнера
docker compose -f docker-compose.prod.yml exec web bash

# Django shell
docker compose -f docker-compose.prod.yml exec web python manage.py shell

# Применить новые миграции (если pull обновлений)
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

## Обновление кода (git pull)

```bash
cd /path/to/KIKIACADEMY
git pull
docker compose -f deploy/docker-compose.prod.yml up -d --build web
```

`entrypoint.sh` автоматически применит миграции и пересоберёт статику.

## Если что-то пошло не так

### SSL не выпускается
- Проверь что DNS A-запись действительно ведёт на сервер: `dig +short твой.домен`
- Порты 80/443 открыты: `sudo ufw allow 80 && sudo ufw allow 443`
- Сначала попробуй staging-сертификат (флаг при запросе)

### Контейнер web падает
```bash
docker compose -f deploy/docker-compose.prod.yml logs web | tail -50
```

### Сброс всего
```bash
docker compose -f deploy/docker-compose.prod.yml down -v   # удалит volumes (БД!)
rm -rf deploy/certbot deploy/nginx/conf.d/* .env
bash deploy/deploy.sh                                       # начать заново
```

## Безопасность

- `.env` содержит секреты — **не коммить в git** (`.gitignore` уже игнорирует)
- `SECRET_KEY` и `POSTGRES_PASSWORD` генерируются случайно при первом деплое
- `SECURE_COOKIES=True` включается автоматически (после HTTPS)
- Backup БД делается через volume `postgres_data`
