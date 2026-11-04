"""Версионирование статических файлов для сброса кеша браузера.

Пример: {% load static_version %}{% static_v 'css/styles.css' %}
даёт /static/css/styles.css?v=1762400000, где число — время изменения файла.
Как только файл меняется, URL меняется вместе с ним, и браузер заново
скачивает стили, не требуя ручного хард-рефреша.
"""

from pathlib import Path

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


def _find_static_file(path):
    """Найти реальный файл статики в DEBUG и после collectstatic."""
    found = finders.find(path)
    if found:
        return Path(found)

    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        candidate = Path(static_root) / path
        if candidate.exists():
            return candidate

    return None


@register.simple_tag
def static_v(path):
    """URL статического файла с версией по дате изменения."""
    url = static(path)
    file_path = _find_static_file(path)

    if file_path is None:
        return url

    try:
        version = int(file_path.stat().st_mtime)
    except OSError:
        return url

    separator = "&" if "?" in url else "?"
    return f"{url}{separator}v={version}"
