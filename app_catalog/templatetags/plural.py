from django import template
from django.utils.translation import gettext as _

register = template.Library()


@register.simple_tag
def plural_forms(count, one, few, many):
    """Выбирает форму слова по числу и переводит её.

    В русском три формы, а blocktrans умеет только две, поэтому на
    страницах с количеством выходит «4 блюд» вместо «4 блюда».

    Пример: {% plural_forms items|length "блюдо" "блюда" "блюд" %}
    """
    number = abs(int(count))
    if number % 10 == 1 and number % 100 != 11:
        form = one
    elif 2 <= number % 10 <= 4 and not 12 <= number % 100 <= 14:
        form = few
    else:
        form = many
    return f"{count} {_(form)}"
