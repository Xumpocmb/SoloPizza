from django.apps import AppConfig
from django.db.models.signals import post_migrate


# Группы сотрудников и их права. Создаются на каждом migrate (миграции с
# данными в git не хранятся), поэтому конфигурация воспроизводима на любой БД.
EMPLOYEE_GROUPS = {
    "СММ": ("can_view_dashboard",),
    "Бухгалтер": ("can_view_statistics", "can_view_reports"),
}


def create_employee_groups(sender, apps, using, **kwargs):
    """Создаёт/обновляет группы сотрудников после применения миграций."""
    if sender.name != "app_order":
        return

    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    Group = apps.get_model("auth", "Group")
    Order = apps.get_model("app_order", "Order")

    codenames = {code for codes in EMPLOYEE_GROUPS.values() for code in codes}
    content_type = ContentType.objects.db_manager(using).get_for_model(Order)
    permissions = {
        permission.codename: permission
        for permission in Permission.objects.using(using).filter(
            content_type=content_type, codename__in=codenames
        )
    }

    for name, group_codenames in EMPLOYEE_GROUPS.items():
        group, _ = Group.objects.db_manager(using).get_or_create(name=name)
        group.permissions.set([permissions[code] for code in group_codenames])


class AppOrderConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_order"
    verbose_name = "Заказ"
    verbose_name_plural = "Заказы"

    def ready(self):
        post_migrate.connect(
            create_employee_groups,
            sender=self,
            dispatch_uid="app_order.create_employee_groups",
        )
