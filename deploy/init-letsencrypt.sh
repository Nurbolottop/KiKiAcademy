#!/bin/bash
# ────────────────────────────────────────────────────────────────
# Получение SSL-сертификата от Let's Encrypt через certbot/webroot
# Использование: ./init-letsencrypt.sh <domain> <email> [staging]
#   staging — использовать тестовые сертификаты (не считаются в лимит)
# ────────────────────────────────────────────────────────────────
set -e

DOMAIN="${1:?Использование: $0 <domain> <email> [staging]}"
EMAIL="${2:?Использование: $0 <domain> <email> [staging]}"
STAGING_FLAG="${3:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTBOT_DIR="$SCRIPT_DIR/certbot"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.prod.yml"
COMPOSE="docker compose -f $COMPOSE_FILE"

echo "→ Создаём директории для certbot…"
mkdir -p "$CERTBOT_DIR/conf" "$CERTBOT_DIR/www"

# Качаем рекомендованные TLS-параметры (один раз)
if [ ! -e "$CERTBOT_DIR/conf/options-ssl-nginx.conf" ]; then
  echo "→ Скачиваем options-ssl-nginx.conf…"
  curl -fsSL https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf \
    > "$CERTBOT_DIR/conf/options-ssl-nginx.conf"
fi
if [ ! -e "$CERTBOT_DIR/conf/ssl-dhparams.pem" ]; then
  echo "→ Скачиваем ssl-dhparams.pem…"
  curl -fsSL https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem \
    > "$CERTBOT_DIR/conf/ssl-dhparams.pem"
fi

# Если сертификат уже есть — пропускаем выпуск
if [ -d "$CERTBOT_DIR/conf/live/$DOMAIN" ] && [ -e "$CERTBOT_DIR/conf/live/$DOMAIN/fullchain.pem" ]; then
  echo "✓ Сертификат для $DOMAIN уже существует, пропускаем выпуск"
else
  echo "→ Запрашиваем сертификат у Let's Encrypt для $DOMAIN…"
  STAGING_ARG=""
  if [ "$STAGING_FLAG" = "staging" ]; then
    STAGING_ARG="--staging"
    echo "  (режим staging — тестовый сертификат)"
  fi

  $COMPOSE run --rm --entrypoint "\
    certbot certonly --webroot -w /var/www/certbot \
      $STAGING_ARG \
      --email $EMAIL \
      -d $DOMAIN \
      --rsa-key-size 4096 \
      --agree-tos \
      --non-interactive \
      --no-eff-email" certbot_kikiacademy

  echo "✓ Сертификат выпущен"
fi

echo "→ Переключаем Nginx на SSL-конфиг…"
DOMAIN="$DOMAIN" envsubst '$DOMAIN' < "$SCRIPT_DIR/nginx/templates/app-ssl.conf.template" \
  > "$SCRIPT_DIR/nginx/conf.d/app.conf"

echo "→ Перезагружаем Nginx…"
$COMPOSE exec nginx_kikiacademy nginx -s reload

echo "✓ Готово! Сайт доступен на https://$DOMAIN"
