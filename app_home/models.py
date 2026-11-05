import random
import string
from datetime import timedelta
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator


def is_staff_user(user) -> bool:
    """Сотрудники и суперпользователи не ограничены правилами приёма заказов."""
    return bool(
        user is not None
        and user.is_authenticated
        and (user.is_staff or user.is_superuser)
    )


class Discount(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название скидки")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Идентификатор скидки", blank=True, null=True)
    percent = models.PositiveIntegerField(verbose_name="Процент скидки")

    def save(self, *args, **kwargs):
        if not self.slug:
            # Преобразуем название в slug (транслитерация и замена пробелов на дефисы)
            from django.utils.text import slugify

            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Скидка"
        verbose_name_plural = "Скидки"

    def __str__(self):
        return f"{self.name} ({self.percent}%)"


class Feedback(models.Model):
    name = models.CharField("Имя", max_length=100)
    phone_regex = RegexValidator(regex=r"^\d{12,}$", message="Номер телефона должен содержать не менее 12 цифр.")
    phone = models.CharField("Номер телефона", max_length=17, validators=[phone_regex])
    message = models.TextField("Сообщение")
    created_at = models.DateTimeField("Дата отправки", auto_now_add=True)

    class Meta:
        verbose_name = "Вопрос/предложение"
        verbose_name_plural = "Вопросы и предложения"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Вопрос/предложение от {self.name}"


class CafeBranch(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название филиала")
    address = models.CharField(max_length=200, verbose_name="Адрес")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    latitude = models.FloatField(verbose_name="Широта", null=True, blank=True)
    longitude = models.FloatField(verbose_name="Долгота", null=True, blank=True)
    delivery_zone = models.JSONField(verbose_name="Зона доставки (полигон)", help_text="Массив координат в формате [[lat1, lng1], [lat2, lng2], ...]", null=True, blank=True)

    # Настройки для печати чеков
    check_font_size = models.PositiveSmallIntegerField(verbose_name="Размер шрифта для чеков", default=18, help_text="Размер шрифта в пикселях")
    check_tape_width = models.PositiveSmallIntegerField(verbose_name="Ширина ленты для чеков", default=80, help_text="Ширина ленты в миллиметрах")
    check_digit = models.PositiveSmallIntegerField(
        verbose_name="Цифра в чеке",
        null=True,
        blank=True,
        validators=[MinValueValidator(0, message="Цифра в чеке должна быть от 0 до 9"), MaxValueValidator(9, message="Цифра в чеке должна быть от 0 до 9")],
        help_text="Первая цифра номера заказа в чеке (0-9). Если не задана — 0.",
    )

    class Meta:
        db_table = "branches"
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"

    def __str__(self):
        return f"Филиал: {self.name}"

    @property
    def first_phone(self):
        """Первый телефон филиала или None.

        Именно all()[0], а не .first(): без Meta.ordering .first() собирает
        новый запрос (order_by("pk")) и не берёт prefetch_related, поэтому
        шапка, подвал и микроразметка выбирали телефоны отдельно каждый раз.
        """
        phones = self.branch_phones.all()
        return phones[0] if phones else None


class CafeBranchPhone(models.Model):
    branch = models.ForeignKey(CafeBranch, on_delete=models.CASCADE, related_name="branch_phones", verbose_name="Филиал")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Номер телефона")

    class Meta:
        db_table = "branch_phones"
        verbose_name = "Телефон филиала"
        verbose_name_plural = "Телефоны филиалов"

    def __str__(self):
        return self.phone or ""

    @property
    def dial(self):
        """Номер в формате, пригодном для ссылки tel: (только цифры и ведущий плюс)."""
        return "".join(ch for ch in (self.phone or "") if ch.isdigit() or ch == "+")


class Vacancy(models.Model):
    title = models.CharField("Название", max_length=100)
    description = models.TextField("Описание", blank=True)
    image = models.ImageField("Фото профессии", upload_to="vacancies/", blank=True, null=True)
    salary = models.CharField("Зарплата", max_length=50, blank=True, null=True)
    benefits = models.TextField("Преимущества (через запятую)", blank=True, null=True)
    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class VacancyApplication(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="applications", verbose_name="Вакансия")
    name = models.CharField("ФИО", max_length=100)
    age = models.PositiveIntegerField(
        "Возраст", validators=[MinValueValidator(16, message="Минимальный возраст - 16 лет"), MaxValueValidator(100, message="Максимальный возраст - 100 лет")]
    )
    phone_regex = RegexValidator(regex=r"^\d{12,}$", message="Номер телефона должен содержать не менее 12 цифр.")
    phone = models.CharField("Номер телефона", max_length=17, validators=[phone_regex])
    experience_years = models.PositiveIntegerField("Стаж работы (лет)", validators=[MaxValueValidator(50, message="Максимальный стаж - 50 лет")])
    work_experience = models.TextField("Опыт работы")
    created_at = models.DateTimeField("Дата отклика", auto_now_add=True)

    class Meta:
        verbose_name = "Отклик на вакансию"
        verbose_name_plural = "Отклики на вакансии"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Отклик на {self.vacancy.title} от {self.name}"


class WorkingHours(models.Model):
    """Модель для указания графика работы"""

    branch = models.ForeignKey(
        CafeBranch, on_delete=models.CASCADE, related_name="working_hours", verbose_name="Филиал", help_text="Филиал, для которого устанавливается график работы"
    )
    day_of_week = models.PositiveIntegerField(
        choices=[(i, ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"][i - 1]) for i in range(1, 8)],
        verbose_name="День недели",
        help_text="День недели (1-7, где 1 - понедельник, 7 - воскресенье)",
    )
    opening_time = models.TimeField(verbose_name="Время открытия", help_text="Время открытия филиала")
    closing_time = models.TimeField(verbose_name="Время закрытия", help_text="Время закрытия филиала")
    is_closed = models.BooleanField(default=False, verbose_name="Закрыт", help_text="Отметьте, если филиал закрыт в этот день")

    class Meta:
        verbose_name = "График работы"
        verbose_name_plural = "Графики работы"
        unique_together = ["branch", "day_of_week"]
        ordering = ["branch", "day_of_week"]

    def __str__(self):
        if self.is_closed:
            return f"{self.branch.name} - {self.get_day_of_week_display()}: Закрыто"
        return f"{self.branch.name} - {self.get_day_of_week_display()}: {self.opening_time} - {self.closing_time}"


class Partner(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название партнера")
    link = models.URLField(verbose_name="Ссылка на партнера", blank=True, null=True)

    class Meta:
        verbose_name = "Партнер"
        verbose_name_plural = "Партнеры"
        ordering = ["name"]

    def __str__(self):
        return self.name


class SiteSettings(models.Model):
    """Настройки сайта: логотип, доступность заказов и снег."""

    logo = models.ImageField(
        "Логотип сайта",
        upload_to="site/",
        blank=True,
        null=True,
        help_text="Показывается в шапке сайта. Если не загружен — используется стандартный логотип.",
    )
    logo_alt = models.CharField("Alt-текст логотипа", max_length=100, default="Solo Pizza")
    orders_available = models.BooleanField(
        "Доступность оформления заказов",
        default=True,
        help_text="Если отключено, пользователи не смогут оформлять новые заказы.",
    )
    snow_enabled = models.BooleanField(
        "Включить снег на сайте",
        default=False,
        help_text="Показывает падающий снег на страницах сайта.",
    )
    updated_at = models.DateTimeField("Дата изменения", auto_now=True)

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return "Настройки сайта"

    @classmethod
    def get_solo(cls):
        """Единственная запись настроек сайта."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def is_orders_available(cls, user=None):
        """Проверить, доступно ли оформление заказов.

        Сотрудники и суперпользователи могут оформлять заказы даже при
        выключенном общесайтовом переключателе.
        """
        if is_staff_user(user):
            return True
        return cls.get_solo().orders_available


class Announcement(models.Model):
    text = models.CharField(max_length=500, verbose_name="Текст объявления")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    class Meta:
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"

    def __str__(self):
        return self.text


class InfoPage(models.Model):
    """Контент страницы «Информация» (информация о компании)."""

    promo_heading = models.CharField(max_length=255, verbose_name="Заголовок промо-блока", default="О компании Solo Pizza")
    promo_description = models.TextField(verbose_name="Описание компании", blank=True, default="Solo Pizza - это не просто пиццерия, это место, где традиции итальянской кухни встречаются с современными технологиями и высоким уровнем сервиса. Мы стремимся создать для наших гостей атмосферу уюта и комфорта, где каждый может насладиться настоящей итальянской пиццей.")

    philosophy_title = models.CharField(max_length=255, verbose_name="Название карточки «Наша философия»", default="Наша философия")
    philosophy_text = models.TextField(verbose_name="Текст карточки «Наша философия»", blank=True, default="Наша миссия - делать вкусную пиццу доступной для каждого жителя Барановичей, сохраняя при этом высокое качество продукции и обслуживания.")

    quality_title = models.CharField(max_length=255, verbose_name="Название карточки «Контроль качества»", default="Контроль качества")
    quality_text = models.TextField(verbose_name="Текст карточки «Контроль качества»", blank=True, default="В Solo Pizza мы уделяем особое внимание качеству используемых продуктов. Мы тщательно отбираем поставщиков и ингредиенты, чтобы наша пицца всегда была вкусной и полезной.")
    quality_training_text = models.TextField(verbose_name="Текст о повышении квалификации поваров", blank=True, default="Наши повара регулярно проходят обучение и совершенствуют свои навыки, чтобы радить вас новыми вкусами и блюдами. Каждая пицца готовится с любовью и вниманием к деталям.")

    delivery_title = models.CharField(max_length=255, verbose_name="Название карточки «Доставка»", default="Доставка")
    delivery_text = models.TextField(verbose_name="Текст карточки «Доставка»", blank=True, default="Мы понимаем, как важно получить заказ вовремя и в идеальном состоянии. Поэтому наша служба доставки работает быстро и эффективно, чтобы ваша пицца приехала к вам горячей и аппетитной.")
    delivery_app_text = models.TextField(verbose_name="Текст о мобильном приложении", blank=True, default="Для удобства наших клиентов мы разработали мобильное приложение, которое можно скачать в Google Play. С его помощью вы можете легко сделать заказ, отследить его статус и получить доступ к специальным предложениям и акциям.")

    address_title = models.CharField(max_length=255, verbose_name="Название карточки «Наш адрес»", default="Наш адрес")
    address_text = models.TextField(verbose_name="Текст карточки «Наш адрес»", blank=True, default="Мы всегда рады видеть вас в нашей пиццерии, где вы можете насладиться не только вкусной едой, но и приятной атмосферой.")

    steps_title = models.CharField(max_length=255, verbose_name="Заголовок блока «Оформление заказа»", default="Оформление заказа")
    step_1_text = models.TextField(verbose_name="Текст шага 1", blank=True, default="После оформления заказа с Вами свяжется оператор для подтверждения заказа.")
    step_2_text = models.TextField(verbose_name="Текст шага 2", blank=True, default="Если заказ не будет подтвержден, он будет отменен.")
    step_3_text = models.TextField(verbose_name="Текст шага 3", blank=True, default="В случае, если с Вами не связались в течении 15ти минут, пожалуйста, перезвоните нам по нашим номерам и сообщите Ваш номер заказа.")

    contacts_title = models.CharField(max_length=255, verbose_name="Заголовок блока «Связаться с нами»", default="Связаться с нами")
    contacts_text = models.TextField(verbose_name="Основной текст блока «Связаться с нами»", blank=True, default="Вы можете связаться с нами по телефонам, указанным на странице контактов, или посетить нашу страницу в Instagram, где мы регулярно публикуем новости, акции и специальные предложения.")
    contacts_text_2 = models.TextField(verbose_name="Дополнительный текст блока «Связаться с нами»", blank=True, default="Также вы можете оставить свой отзыв или предложение на странице обратной связи. Мы ценим мнение каждого клиента и стремимся становиться лучше с каждым днем.")

    class Meta:
        verbose_name = "Информация"
        verbose_name_plural = "Информация"

    @classmethod
    def get_solo(cls):
        """Единая запись контента страницы «Информация»."""
        info, created = cls.objects.get_or_create(pk=1)
        return info


def generate_unique_code():
    """Generate a unique certificate code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Certificate.objects.filter(code=code).exists():
            return code


class Certificate(models.Model):
    code = models.CharField(max_length=8, unique=True, verbose_name="Уникальный код сертификата", default=generate_unique_code)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    expires_at = models.DateTimeField(verbose_name="Срок действия")
    is_used = models.BooleanField(default=False, verbose_name="Использован")
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата использования")

    class Meta:
        verbose_name = "Сертификат"
        verbose_name_plural = "Сертификаты"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # Set expiration date to 3 months from creation if not already set
        if not self.expires_at:
            from django.utils import timezone
            self.expires_at = timezone.now() + timedelta(days=90)  # 3 months ~ 90 days
        super().save(*args, **kwargs)

    def __str__(self):
        status = "использован" if self.is_used else "действителен"
        return f"Сертификат {self.code} ({status})"
