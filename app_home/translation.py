from modeltranslation.translator import register, TranslationOptions

from .models import CafeBranch, Discount, Partner, Vacancy


@register(Vacancy)
class VacancyTranslationOptions(TranslationOptions):
    fields = ("title", "description", "salary", "benefits")


@register(CafeBranch)
class CafeBranchTranslationOptions(TranslationOptions):
    fields = ("name", "address")


@register(Partner)
class PartnerTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Discount)
class DiscountTranslationOptions(TranslationOptions):
    fields = ("name",)