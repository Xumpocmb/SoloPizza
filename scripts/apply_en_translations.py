"""Fill *_en fields of the catalog fixture from scripts/en_translations.py.

Usage:
    python scripts/apply_en_translations.py fixtures/27-09-2026/catalog.json
    python scripts/apply_en_translations.py fixtures/27-09-2026/catalog.json --db
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.en_translations import CATEGORY_TRANSLATIONS, TRANSLATIONS


def apply_to_fixture(path):
    with open(path, encoding="utf-8") as f:
        objects = json.load(f)

    missing_products = []
    missing_categories = []
    unknown_slugs = set(TRANSLATIONS)
    filled = 0

    for obj in objects:
        fields = obj.get("fields", {})
        if obj["model"] == "app_catalog.product":
            slug = fields.get("slug")
            unknown_slugs.discard(slug)
            if slug not in TRANSLATIONS:
                missing_products.append((obj.get("pk"), slug))
                continue
            name_en, description_en = TRANSLATIONS[slug]
            if description_en is None:
                description_en = fields.get("description_ru")
            fields["name_en"] = name_en
            fields["description_en"] = description_en
            filled += 1
        elif obj["model"] == "app_catalog.category":
            slug = fields.get("slug")
            if slug not in CATEGORY_TRANSLATIONS:
                missing_categories.append((obj.get("pk"), slug))
                continue
            fields["name_en"] = CATEGORY_TRANSLATIONS[slug]
            filled += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(objects, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"filled {filled} objects in {path}")
    if missing_products:
        print("products without translation:", missing_products)
    if missing_categories:
        print("categories without translation:", missing_categories)
    if unknown_slugs:
        print("translations not used by the fixture:", sorted(unknown_slugs))


def apply_to_db():
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SoloPizza.settings")
    django.setup()

    from app_catalog.models import Category, Product

    for category in Category.objects.all():
        if category.slug in CATEGORY_TRANSLATIONS:
            category.name_en = CATEGORY_TRANSLATIONS[category.slug]
            category.save(update_fields=["name_en"])

    for product in Product.objects.all():
        if product.slug not in TRANSLATIONS:
            print("product without translation:", product.pk, product.slug)
            continue
        name_en, description_en = TRANSLATIONS[product.slug]
        product.name_en = name_en
        product.description_en = (
            product.description_ru if description_en is None else description_en
        )
        product.save(update_fields=["name_en", "description_en"])

    print("database updated")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture")
    parser.add_argument("--db", action="store_true")
    args = parser.parse_args()

    apply_to_fixture(args.fixture)
    if args.db:
        apply_to_db()


if __name__ == "__main__":
    main()
