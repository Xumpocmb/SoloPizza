"""Правила приёма заказов с учётом графика работы филиала.

Заказы принимаются только во время смены филиала и прекращаются за
``ORDER_CUTOFF`` до закрытия. Сотрудники и суперпользователи могут оформлять
заказы в любое время.

Смена может переходить через полночь: если время закрытия меньше либо равно
времени открытия, считается, что филиал закрывается на следующий день.
Поэтому ранним утром проверяется ещё и график предыдущего дня.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from django.utils import timezone

from app_home.models import CafeBranch, WorkingHours, is_staff_user

ORDER_CUTOFF = timedelta(minutes=30)


@dataclass(frozen=True)
class Shift:
    """Смена филиала с конкретными датой и временем открытия/закрытия."""

    schedule: WorkingHours
    opens_at: datetime
    closes_at: datetime

    @property
    def last_order_at(self) -> datetime:
        """Момент, после которого заказы от пользователей не принимаются."""
        return self.closes_at - ORDER_CUTOFF


def _make_aware(day: date, value: time) -> datetime:
    return timezone.make_aware(
        datetime.combine(day, value),
        timezone.get_current_timezone(),
    )


def _shift_starting_on(day: date, schedule: WorkingHours) -> Shift:
    opens_at = _make_aware(day, schedule.opening_time)
    closes_at = _make_aware(day, schedule.closing_time)
    if schedule.closing_time <= schedule.opening_time:
        closes_at += timedelta(days=1)
    return Shift(schedule=schedule, opens_at=opens_at, closes_at=closes_at)


def _schedules_by_day(branch: CafeBranch) -> dict[int, WorkingHours]:
    # Если филиал пришёл с prefetch_related("working_hours"), запроса к БД не будет.
    return {row.day_of_week: row for row in branch.working_hours.all()}


def _now(at: datetime | None = None) -> datetime:
    return timezone.localtime(at) if at is not None else timezone.localtime()


def get_current_shift(branch: CafeBranch, at: datetime | None = None) -> Shift | None:
    """Возвращает смену, в которую попадает момент ``at``, или ``None``."""
    if branch is None:
        return None

    now = _now(at)
    schedules = _schedules_by_day(branch)

    candidates = []
    # Вчерашняя смена нужна для филиалов, которые работают после полуночи.
    for day in (now.date() - timedelta(days=1), now.date()):
        schedule = schedules.get(day.isoweekday())
        if schedule is None or schedule.is_closed:
            continue
        shift = _shift_starting_on(day, schedule)
        if shift.opens_at <= now < shift.closes_at:
            candidates.append(shift)

    if not candidates:
        return None
    return max(candidates, key=lambda shift: shift.opens_at)


def is_order_time_allowed(
    branch: CafeBranch | None,
    user=None,
    at: datetime | None = None,
) -> bool:
    """Можно ли оформить заказ в филиале в момент ``at``."""
    if is_staff_user(user):
        return True
    if branch is None:
        return True

    shift = get_current_shift(branch, at)
    if shift is None:
        return False

    return _now(at) < shift.last_order_at


def _schedule_for_message(branch: CafeBranch, at: datetime | None = None) -> WorkingHours | None:
    """График, который стоит показать пользователю в сообщении об отказе."""
    shift = get_current_shift(branch, at)
    if shift is not None:
        return shift.schedule

    if branch is None:
        return None

    now = _now(at)
    return _schedules_by_day(branch).get(now.date().isoweekday())


def order_time_restriction_message(branch: CafeBranch | None, at: datetime | None = None) -> str:
    """Понятное пользователю объяснение, почему заказ сейчас нельзя оформить."""
    schedule = _schedule_for_message(branch, at)

    if schedule is None:
        return "Заказы временно не принимаются: график работы филиала не установлен."

    if schedule.is_closed:
        branch_name = f" «{branch.name}»" if branch is not None else ""
        return f"Заказы временно не принимаются: филиал{branch_name} сегодня не работает."

    branch_name = f" «{branch.name}»" if branch is not None else ""
    cutoff_minutes = int(ORDER_CUTOFF.total_seconds() // 60)
    return (
        f"Филиал{branch_name} принимает заказы с {schedule.opening_time:%H:%M} "
        f"до {schedule.closing_time:%H:%M}. Приём заказов прекращается "
        f"за {cutoff_minutes} минут до закрытия."
    )
