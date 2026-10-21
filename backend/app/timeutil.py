from calendar import monthrange
from datetime import datetime, date
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def today_ist() -> date:
    return datetime.now(IST).date()


def month_bounds(d: date) -> tuple[date, date]:
    return (
        d.replace(day=1),
        d.replace(day=monthrange(d.year, d.month)[1]),
    )


def months_back(d: date, n: int) -> date:
    """Return the first day of the month n months before d."""
    y, m = d.year, d.month - n

    while m <= 0:
        m += 12
        y -= 1

    return date(y, m, 1)
