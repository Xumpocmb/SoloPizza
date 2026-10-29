import re

from django.core.exceptions import ValidationError

def validate_phone_number_length(value):
    """
    Валидатор для очистки номера телефона и проверки его длины.
    """
    cleaned_phone_number = re.sub(r'[^0-9]', '', value)

    if len(cleaned_phone_number) < 12:
        raise ValidationError("Номер телефона должен содержать минимум 12 цифр: код страны, код оператора и сам номер.\nПример: 375 (XX) YYY-YY-YY\nПробелы, скобки, тире - не нужны. Пишите только цифры.")