from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator


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

    class Meta:
        db_table = "branches"
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"

    def __str__(self):
        return f"Филиал: {self.name}"


class CafeBranchPhone(models.Model):
    branch = models.ForeignKey(CafeBranch, on_delete=models.CASCADE, related_name="branch_phones", verbose_name="Филиал")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Номер телефона")

    class Meta:
        db_table = "branch_phones"
        verbose_name = "Телефон филиала"
        verbose_name_plural = "Телефоны филиалов"


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


class OrderAvailability(models.Model):
    """Модель для управления доступностью оформления заказов"""

    is_available = models.BooleanField(default=True, verbose_name="Доступность оформления заказов", help_text="Если отключено, пользователи не смогут оформлять новые заказы")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата последнего изменения")

    class Meta:
        verbose_name = "Доступность заказов"
        verbose_name_plural = "Доступность заказов"

    def __str__(self):
        status = "доступно" if self.is_available else "недоступно"
        return f"Оформление заказов: {status}"

    @classmethod
    def toggle_availability(cls):
        """Переключить доступность заказов"""
        obj, created = cls.objects.get_or_create(pk=1)
        obj.is_available = not obj.is_available
        obj.save()
        return obj

    @classmethod
    def is_orders_available(cls):
        """Проверить, доступно ли оформление заказов"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj.is_available


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


class SnowSettings(models.Model):
    is_enabled = models.BooleanField(default=False, verbose_name="Включить снег на сайте")

    class Meta:
        verbose_name = "Настройка снега"
        verbose_name_plural = "Настройки снега"

    def __str__(self):
        return "Снег включен" if self.is_enabled else "Снег выключен"


class Marquee(models.Model):
    text = models.CharField(max_length=500, verbose_name="Текст бегущей строки")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Бегущая строка"
        verbose_name_plural = "Бегущие строки"

    def __str__(self):
        return self.text
