#!/bin/sh
set -e

echo "→ Ждём PostgreSQL ($POSTGRES_HOST:$POSTGRES_PORT)…"
until nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done
echo "✓ PostgreSQL готов"

echo "→ Применяем миграции…"
python manage.py migrate --noinput

echo "→ Собираем статику…"
python manage.py collectstatic --noinput

echo "→ Компилируем переводы…"
python manage.py compilemessages --locale ky || true

echo "→ Запускаем приложение…"
exec "$@"
