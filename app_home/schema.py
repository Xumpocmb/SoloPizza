"""Микроразметка Schema.org для главной страницы.

Раньше JSON-LD был записан в шаблоне руками, из-за чего адреса, телефон,
координаты и режим работы расходились с базой. Теперь всё собирается
из филиалов и их графика работы.
"""

import json

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

SITE_URL = "https://solopizza.by"
DEFAULT_REGION = "Брестская область"
DEFAULT_POSTAL_CODE = "225400"
DEFAULT_COUNTRY = "BY"
DEFAULT_LOCALITY = "Барановичи"

# Экранируем символы, которые нельзя оставлять внутри <script>, но сохраняем
# валидный JSON — так же делает django.forms.widgets.json_script.
_JSON_ESCAPES = str.maketrans({"<": "\\u003C", ">": "\\u003E", "&": "\\u0026"})


def _split_address(address):
    """'г. Барановичи, ул. Ленина 9/1' -> ('Барановичи', 'ул. Ленина 9/1')."""
    if "," in address:
        locality, street = address.split(",", 1)
        locality = locality.strip()
        if locality.startswith("г. "):
            locality = locality[3:]
        return locality or DEFAULT_LOCALITY, street.strip()
    return DEFAULT_LOCALITY, address.strip()


def _postal_address(branch):
    locality, street = _split_address(branch.address)
    return {
        "@type": "PostalAddress",
        "streetAddress": street,
        "addressLocality": locality,
        "addressRegion": DEFAULT_REGION,
        "postalCode": DEFAULT_POSTAL_CODE,
        "addressCountry": DEFAULT_COUNTRY,
    }


def _opening_hours(branches):
    """Часы работы всех филиалов, сгруппированные по одинаковому времени."""
    grouped = {}
    for branch in branches:
        for working in branch.working_hours.all():
            if working.is_closed:
                continue
            hours = (working.opening_time.strftime("%H:%M"), working.closing_time.strftime("%H:%M"))
            days = grouped.setdefault(hours, set())
            days.add(WEEKDAYS[working.day_of_week - 1])

    specification = []
    for (opens, closes), days in grouped.items():
        specification.append(
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": sorted(days, key=WEEKDAYS.index),
                "opens": opens,
                "closes": closes,
            }
        )
    return specification


def restaurant_schema(branches, selected_branch):
    """Собирает разметку ресторана по всем активным филиалам.

    Адреса и режим работы — по всем филиалам, телефон и координаты —
    по выбранному в шапке, чтобы совпадать с тем, что видит посетитель.
    """
    if hasattr(branches, "prefetch_related"):
        branches = branches.prefetch_related("working_hours", "branch_phones")
    branches = list(branches)

    schema = {
        "@context": "http://schema.org",
        "@type": "Restaurant",
        "name": "SoloPizza",
        "address": [_postal_address(branch) for branch in branches],
        "url": SITE_URL,
        "servesCuisine": "Пицца",
        "priceRange": "$$",
        "hasMenu": {
            "@type": "Menu",
            "url": f"{SITE_URL}/catalog/",
        },
    }

    if selected_branch:
        phone = selected_branch.first_phone
        if phone:
            schema["telephone"] = phone.dial
        if selected_branch.latitude and selected_branch.longitude:
            schema["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": str(selected_branch.latitude),
                "longitude": str(selected_branch.longitude),
            }

    hours = _opening_hours(branches)
    if hours:
        schema["openingHoursSpecification"] = hours

    return schema


def render_json_ld(schema):
    """Готовая строка для <script type="application/ld+json">."""
    return json.dumps(schema, ensure_ascii=False, indent=4).translate(_JSON_ESCAPES)
