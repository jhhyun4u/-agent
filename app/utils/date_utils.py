"""날짜 계산 유틸리티 — D-day, 잔여일, 마감 판정"""

from datetime import date, datetime, timezone, timedelta

# KST 타임존 (UTC+9)
KST = timezone(timedelta(hours=9))


def calc_dday(
    deadline: str | date | datetime,
    base: str | date | datetime | None = None,
) -> int:
    """마감일까지 잔여일 계산 (D-day).

    Args:
        deadline: 마감일 (YYYY-MM-DD 문자열, date, datetime)
        base: 기준일 (기본값: 오늘 KST 날짜)

    Returns:
        양수=남은 일수, 0=당일, 음수=초과 일수
    """
    deadline_date = _to_date(deadline)
    base_date = _to_date(base) if base else datetime.now(KST).date()
    return (deadline_date - base_date).days


def calc_progress(total: int, completed: int) -> float:
    """진도율 계산 (%).

    Args:
        total: 전체 마일스톤 수
        completed: 완료 마일스톤 수

    Returns:
        진도율 (0.0~100.0). total=0이면 0.0 반환.
    """
    if total <= 0:
        return 0.0
    return round(completed / total * 100, 1)


def calc_budget_rate(total: int | float, used: int | float) -> float:
    """예산 집행률 계산 (%).

    Args:
        total: 총 예산
        used: 집행금액

    Returns:
        집행률 (%). total=0이면 0.0. 100% 초과 가능.
    """
    if total <= 0:
        return 0.0
    return round(used / total * 100, 1)


def deadline_alert_level(days_left: int) -> str | None:
    """잔여일 기반 알림 등급 결정.

    Returns:
        "info" (D-7), "warning" (D-3), "danger" (D-0 이하), None (해당 없음)
    """
    if days_left <= 0:
        return "danger"
    if days_left <= 3:
        return "warning"
    if days_left <= 7:
        return "info"
    return None


def _to_date(value: str | date | datetime) -> date:
    """문자열/datetime을 date로 변환."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)
