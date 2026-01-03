# app_user/management/commands/create_random_users.py
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone


class Command(BaseCommand):
    help = "Создает 50 случайных пользователей с русскими именами"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=50, help="Количество создаваемых пользователей (по умолчанию 50)")
        parser.add_argument("--clear", action="store_true", help="Удалить всех существующих пользователей перед созданием")

    def handle(self, *args, **options):
        count = options["count"]
        clear = options["clear"]

        # Русские имена и фамилии
        male_first_names = [
            "Александр",
            "Алексей",
            "Андрей",
            "Антон",
            "Артем",
            "Борис",
            "Вадим",
            "Валентин",
            "Валерий",
            "Василий",
            "Виктор",
            "Виталий",
            "Владимир",
            "Владислав",
            "Геннадий",
            "Георгий",
            "Григорий",
            "Даниил",
            "Денис",
            "Дмитрий",
            "Евгений",
            "Егор",
            "Иван",
            "Игорь",
            "Илья",
            "Кирилл",
            "Константин",
            "Лев",
            "Леонид",
            "Максим",
            "Михаил",
            "Никита",
            "Николай",
            "Олег",
            "Павел",
            "Петр",
            "Роман",
            "Сергей",
            "Станислав",
            "Степан",
            "Тимофей",
            "Федор",
            "Юрий",
            "Ярослав",
        ]

        female_first_names = [
            "Александра",
            "Алена",
            "Алина",
            "Алиса",
            "Алла",
            "Анастасия",
            "Ангелина",
            "Анжела",
            "Анна",
            "Валентина",
            "Валерия",
            "Варвара",
            "Вера",
            "Вероника",
            "Виктория",
            "Галина",
            "Дарья",
            "Диана",
            "Ева",
            "Евгения",
            "Екатерина",
            "Елена",
            "Елизавета",
            "Жанна",
            "Зоя",
            "Инна",
            "Ирина",
            "Кира",
            "Кристина",
            "Ксения",
            "Лариса",
            "Лидия",
            "Любовь",
            "Людмила",
            "Маргарита",
            "Марина",
            "Мария",
            "Надежда",
            "Наталья",
            "Ника",
            "Нина",
            "Оксана",
            "Олеся",
            "Ольга",
            "Полина",
            "Раиса",
            "Регина",
            "Светлана",
            "София",
            "Тамара",
            "Татьяна",
            "Ульяна",
            "Юлия",
            "Яна",
        ]

        last_names = [
            "Иванов",
            "Смирнов",
            "Кузнецов",
            "Попов",
            "Васильев",
            "Петров",
            "Соколов",
            "Михайлов",
            "Новиков",
            "Федоров",
            "Морозов",
            "Волков",
            "Алексеев",
            "Лебедев",
            "Семенов",
            "Егоров",
            "Павлов",
            "Козлов",
            "Степанов",
            "Николаев",
            "Орлов",
            "Андреев",
            "Макаров",
            "Никитин",
            "Захаров",
            "Зайцев",
            "Соловьев",
            "Борисов",
            "Яковлев",
            "Григорьев",
            "Романов",
            "Воробьев",
            "Сергеев",
            "Кузьмин",
            "Фролов",
            "Александров",
            "Дмитриев",
            "Королев",
            "Гусев",
            "Киселев",
            "Ильин",
            "Максимов",
            "Поляков",
            "Сорокин",
            "Виноградов",
            "Ковалев",
            "Белов",
            "Медведев",
            "Антонов",
            "Тарасов",
        ]

        # Телефонные коды и форматы
        phone_codes = [
            "901",
            "902",
            "903",
            "904",
            "905",
            "906",
            "915",
            "916",
            "917",
            "918",
            "919",
            "925",
            "926",
            "927",
            "928",
            "929",
            "937",
            "938",
            "939",
            "950",
            "951",
            "952",
            "953",
            "960",
            "961",
            "962",
            "963",
            "964",
            "965",
            "966",
            "967",
            "968",
            "969",
            "977",
            "978",
            "979",
            "980",
            "981",
            "982",
            "983",
            "984",
            "985",
            "986",
            "987",
            "988",
            "989",
            "991",
            "992",
            "993",
            "994",
            "995",
            "996",
            "999",
        ]

        # Адреса в Москве
        moscow_districts = ["ЦАО", "САО", "СВАО", "ВАО", "ЮВАО", "ЮАО", "ЮЗАО", "ЗАО", "СЗАО"]

        streets = [
            "ул. Тверская",
            "ул. Арбат",
            "ул. Новый Арбат",
            "ул. Пятницкая",
            "ул. Большая Дмитровка",
            "ул. Маросейка",
            "ул. Покровка",
            "ул. Мясницкая",
            "ул. Никольская",
            "ул. Ильинка",
            "ул. Пречистенка",
            "ул. Остоженка",
            "ул. Знаменка",
            "ул. Волхонка",
            "ул. Воздвиженка",
            "ул. Большая Якиманка",
            "ул. Большая Полянка",
            "пр. Ленинский",
            "пр. Мичуринский",
            "ул. Профсоюзная",
            "ул. Обручева",
            "ул. Нахимовский",
            "ул. Севастопольский",
            "ул. Нагатинская",
            "ул. Варшавское шоссе",
            "ул. Каширское шоссе",
            "ул. Дмитрия Ульянова",
            "ул. Вавилова",
            "ул. Кржижановского",
            "ул. Гарибальди",
            "ул. Удальцова",
            "ул. Лобачевского",
            "ул. Минская",
            "ул. Кутузовский проспект",
            "ул. Можайское шоссе",
            "ул. Рублевское шоссе",
            "ул. Аминьевское шоссе",
            "ул. Ярцевская",
            "ул. Молодогвардейская",
            "ул. Кунцевская",
        ]

        if clear:
            # Удаляем всех пользователей кроме суперпользователей
            users_to_delete = User.objects.filter(is_superuser=False)
            deleted_count = users_to_delete.count()
            users_to_delete.delete()
            self.stdout.write(self.style.WARNING(f"Удалено {deleted_count} пользователей"))

        created_count = 0

        for i in range(count):
            # Определяем пол (50/50)
            is_male = random.choice([True, False])
            base_last_name = random.choice(last_names)

            if is_male:
                first_name = random.choice(male_first_names)
                last_name = base_last_name
            else:
                first_name = random.choice(female_first_names)
                if base_last_name.endswith('ий'):
                    last_name = base_last_name[:-2] + 'ая'
                else:
                    last_name = base_last_name + "а"

            # Генерируем уникальный username
            username_base = f"{first_name.lower()}.{base_last_name.lower()}"
            username = username_base

            # Проверяем уникальность
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{username_base}{counter}"
                counter += 1

            # Генерируем email
            email_domain = random.choice(["gmail.com", "yandex.ru", "mail.ru", "outlook.com"])
            email = f"{username}@{email_domain}"

            # Генерируем телефон
            phone_code = random.choice(phone_codes)
            phone_number = f"7{phone_code}{random.randint(1000000, 9999999)}"

            # Генерируем адрес
            district = random.choice(moscow_districts)
            street = random.choice(streets)
            building = random.randint(1, 200)
            apartment = random.randint(1, 300)
            address = f"Москва, {district}, {street}, д. {building}, кв. {apartment}"

            # Генерируем дату регистрации (от 1 дня до 3 лет назад)
            days_ago = random.randint(1, 365 * 3)
            date_joined = timezone.now() - timedelta(days=days_ago)

            # Случайный last_login (50% пользователей заходили недавно)
            if random.choice([True, False]):
                last_login_days = random.randint(1, 30)
                last_login = timezone.now() - timedelta(days=last_login_days)
            else:
                last_login = None

            # Создаем пользователя
            try:
                user = User.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_superuser=False,
                    is_staff=random.choice([True, False]),  # 50% персонал
                    is_active=True,
                    date_joined=date_joined,
                    last_login=last_login,
                )

                # Устанавливаем случайный пароль
                user.set_password(f"password{random.randint(1000, 9999)}")

                # Устанавливаем кастомные поля (если они есть через add_to_class)
                if hasattr(user, "phone"):
                    user.phone = phone_number
                if hasattr(user, "address"):
                    user.address = address

                user.save()

                created_count += 1

                self.stdout.write(self.style.SUCCESS(f"Создан пользователь #{i+1}: {username} ({first_name} {last_name})"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка при создании пользователя #{i+1}: {e}"))

        # Создаем несколько тестовых суперпользователей
        test_superusers = [
            {"username": "admin", "password": "admin123", "email": "admin@solo-pizza.ru", "first_name": "Администратор", "last_name": "Системы"},
            {"username": "manager", "password": "manager123", "email": "manager@solo-pizza.ru", "first_name": "Менеджер", "last_name": "Ресторана"},
            {"username": "testuser", "password": "test123", "email": "test@example.com", "first_name": "Тестовый", "last_name": "Пользователь"},
        ]

        for superuser_data in test_superusers:
            if not User.objects.filter(username=superuser_data["username"]).exists():
                user = User.objects.create_superuser(username=superuser_data["username"], email=superuser_data["email"], password=superuser_data["password"])
                user.first_name = superuser_data["first_name"]
                user.last_name = superuser_data["last_name"]
                user.save()

                self.stdout.write(self.style.WARNING(f'Создан суперпользователь: {superuser_data["username"]}'))

        self.stdout.write(self.style.SUCCESS(f"\nУспешно создано {created_count} пользователей из {count} запланированных"))

        # Выводим статистику
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        staff_users = User.objects.filter(is_staff=True).count()

        self.stdout.write(
            self.style.SUCCESS(
                f"\nОбщая статистика:\n" f"Всего пользователей в системе: {total_users}\n" f"Активных пользователей: {active_users}\n" f"Персонала (is_staff): {staff_users}"
            )
        )
