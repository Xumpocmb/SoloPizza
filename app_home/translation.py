from modeltranslation.translator import register, TranslationOptions

from .models import CafeBranch, Discount, InfoPage, Partner, Vacancy


@register(Vacancy)
class VacancyTranslationOptions(TranslationOptions):
    fields = ("title", "description")


@register(CafeBranch)
class CafeBranchTranslationOptions(TranslationOptions):
    fields = ("name", "address")


@register(Partner)
class PartnerTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Discount)
class DiscountTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(InfoPage)
class InfoPageTranslationOptions(TranslationOptions):
    fields = (
        "promo_heading",
        "promo_description",
        "philosophy_title",
        "philosophy_text",
        "quality_title",
        "quality_text",
        "quality_training_text",
        "delivery_title",
        "delivery_text",
        "delivery_app_text",
        "address_title",
        "address_text",
        "steps_title",
        "step_1_text",
        "step_2_text",
        "step_3_text",
        "contacts_title",
        "contacts_text",
        "contacts_text_2",
    )