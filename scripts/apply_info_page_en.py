"""Fill the *_en fields of InfoPage with English translations.

The Russian text stays in the base and *_ru fields; only *_en is touched.

Usage:
    python scripts/apply_info_page_en.py
    python scripts/apply_info_page_en.py --fixture fixtures/11-11-2026/app_home_2026-11-11.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TRANSLATIONS = {
    "promo_heading": "About Solo Pizza",
    "promo_description": (
        "Solo Pizza is more than just a pizzeria. It is a place where Italian culinary "
        "traditions meet modern technology and a high level of service. We strive to create "
        "an atmosphere of warmth and comfort for our guests, where everyone can enjoy "
        "authentic Italian pizza."
    ),
    "philosophy_title": "Our Philosophy",
    "philosophy_text": (
        "Our mission is to make delicious pizza accessible to every resident of Baranovichi "
        "while maintaining high quality of products and service."
    ),
    "quality_title": "Quality Control",
    "quality_text": (
        "At Solo Pizza, we pay special attention to the quality of the ingredients we use. "
        "We carefully select suppliers and ingredients so that our pizza is always tasty and wholesome."
    ),
    "quality_training_text": (
        "Our chefs regularly undergo training and hone their skills to delight you with new "
        "flavours and dishes. Every pizza is made with love and attention to detail."
    ),
    "delivery_title": "Delivery",
    "delivery_text": (
        "We understand how important it is to receive your order on time and in perfect condition. "
        "That is why our delivery service works quickly and efficiently, so that your pizza arrives "
        "hot and appetising."
    ),
    "delivery_app_text": (
        "For the convenience of our customers, we have developed a mobile app that can be downloaded "
        "from Google Play. With it, you can easily place an order, track its status and get access "
        "to special offers and promotions."
    ),
    "address_title": "Our Address",
    "address_text": (
        "We are always happy to see you at our pizzeria, where you can enjoy not only delicious food "
        "but also a pleasant atmosphere."
    ),
    "steps_title": "Placing an Order",
    "step_1_text": (
        "After you place an order, an operator will contact you to confirm it."
    ),
    "step_2_text": "If the order is not confirmed, it will be cancelled.",
    "step_3_text": (
        "If you have not been contacted within 15 minutes, please call us at one of our numbers "
        "and provide your order number."
    ),
    "contacts_title": "Contact Us",
    "contacts_text": (
        "You can contact us by phone using the numbers on the contacts page, or visit our Instagram "
        "page, where we regularly post news, promotions and special offers."
    ),
    "contacts_text_2": (
        "You can also leave your feedback or suggestion on the feedback page. We value every "
        "customer's opinion and strive to improve every day."
    ),
}


def apply_to_db():
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SoloPizza.settings")
    django.setup()

    from app_home.models import InfoPage

    info = InfoPage.get_solo()
    update_fields = []
    for field, value in TRANSLATIONS.items():
        setattr(info, f"{field}_en", value)
        update_fields.append(f"{field}_en")
    info.save(update_fields=update_fields)

    print(f"updated InfoPage pk={info.pk}: {len(update_fields)} English fields")


def apply_to_fixture(path):
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        objects = json.load(f)

    updated = 0
    for obj in objects:
        if obj["model"] != "app_home.infopage":
            continue
        fields = obj.setdefault("fields", {})
        for field, value in TRANSLATIONS.items():
            fields[f"{field}_en"] = value
            updated += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(objects, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"updated {updated} English fields in {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fixture",
        help="Also update the InfoPage object in this JSON fixture.",
    )
    args = parser.parse_args()

    apply_to_db()
    if args.fixture:
        apply_to_fixture(args.fixture)


if __name__ == "__main__":
    main()
