from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator


class Feedback(models.Model):
    name = models.CharField("Имя", max_length=100)
    phone_regex = RegexValidator(
        regex=r'^\d{12,}$',
        message="Номер телефона должен содержать не менее 12 цифр."
    )
    phone = models.CharField(
        "Номер телефона", 
        max_length=17, 
        validators=[phone_regex]
    )
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
    salary = models.CharField("Зарплата", max_length=50, blank=True)
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
        "Возраст", 
        validators=[MinValueValidator(16, message="Минимальный возраст - 16 лет"), 
                   MaxValueValidator(100, message="Максимальный возраст - 100 лет")]
    )
    phone_regex = RegexValidator(
        regex=r'^\d{12,}$',
        message="Номер телефона должен содержать не менее 12 цифр."
    )
    phone = models.CharField(
        "Номер телефона", 
        max_length=17, 
        validators=[phone_regex]
    )
    experience_years = models.PositiveIntegerField(
        "Стаж работы (лет)", 
        validators=[MaxValueValidator(50, message="Максимальный стаж - 50 лет")]
    )
    work_experience = models.TextField("Опыт работы")
    created_at = models.DateTimeField("Дата отклика", auto_now_add=True)
    
    class Meta:
        verbose_name = "Отклик на вакансию"
        verbose_name_plural = "Отклики на вакансии"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Отклик на {self.vacancy.title} от {self.name}"
