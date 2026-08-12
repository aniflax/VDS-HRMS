"""Shared timezone helpers.

All "now" / "today" values used by the backend are India local time
(IST, UTC+05:30). The frontend then renders them with `timeZone:
"Asia/Kolkata"`, so the whole stack is consistent. No UTC anywhere.

Models and services import from here to avoid importing from
`app.services.attendance` (which pulls in models and would create a
circular import).
"""
from datetime import datetime, date
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def get_local_now() -> datetime:
    """Return the current India local time as a naive datetime.

    Naive on purpose: the DB columns are `TIMESTAMP WITHOUT TIME ZONE`,
    so storing/returning a naive IST value keeps the rest of the app
    simple and matches the user requirement that "no UTC is maintained
    anywhere".
    """
    return datetime.now(IST).replace(tzinfo=None)


def get_local_today() -> date:
    """Return today's date in India local time."""
    return get_local_now().date()
