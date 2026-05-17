import re

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


_YT_RE = re.compile(r'(?:youtu\.be/|youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/))([A-Za-z0-9_-]{6,})')
_VIMEO_RE = re.compile(r'vimeo\.com/(?:video/)?(\d+)')


@register.filter(name='video_embed_url')
def video_embed_url(url: str) -> str:
    """Превращает URL YouTube/Vimeo в URL для embed-iframe."""
    if not url:
        return ''
    m = _YT_RE.search(url)
    if m:
        return f'https://www.youtube.com/embed/{m.group(1)}'
    m = _VIMEO_RE.search(url)
    if m:
        return f'https://player.vimeo.com/video/{m.group(1)}'
    return url


@register.simple_tag
def video_iframe(url: str):
    embed = video_embed_url(url)
    if not embed:
        return ''
    html = (
        f'<div class="video-embed">'
        f'<iframe src="{embed}" frameborder="0" allowfullscreen '
        f'allow="autoplay; encrypted-media; picture-in-picture"></iframe>'
        f'</div>'
    )
    return mark_safe(html)
