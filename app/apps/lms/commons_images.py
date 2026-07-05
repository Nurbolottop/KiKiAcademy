"""Загрузка бесплатных фотографий с Wikimedia Commons для наполнения уроков.

Ищет по запросу растровое фото (свободная лицензия), скачивает и отдаёт байты.
Используется seed-командами. Против rate-limit — повторы с бэкоффом.
"""
import json
import time
import urllib.parse
import urllib.request

UA = {'User-Agent': 'KIKIAcademyBot/1.0 (internal training; contact admin)'}
COMMONS_API = 'https://commons.wikimedia.org/w/api.php'


def _get(url, timeout=60, retries=4):
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def fetch_commons_image(query, timeout=60):
    """Возвращает (bytes, source_url) первого подходящего фото или (None, None)."""
    params = urllib.parse.urlencode({
        'action': 'query', 'generator': 'search',
        'gsrsearch': f'filetype:bitmap {query}',
        'gsrnamespace': '6', 'gsrlimit': '8',
        'prop': 'imageinfo', 'iiprop': 'url|mime', 'iiurlwidth': '1400',
        'format': 'json',
    })
    raw = _get(f'{COMMONS_API}?{params}', timeout)
    if not raw:
        return None, None
    try:
        data = json.loads(raw)
    except Exception:
        return None, None
    pages = (data.get('query') or {}).get('pages') or {}
    for p in sorted(pages.values(), key=lambda x: x.get('index', 999)):
        info = (p.get('imageinfo') or [{}])[0]
        mime = info.get('mime', '')
        url = info.get('thumburl') or info.get('url')
        if not url or not mime.startswith('image/') or 'svg' in mime:
            continue
        img = _get(url, timeout)
        if img and len(img) > 5000:
            return img, info.get('descriptionurl') or url
    return None, None
