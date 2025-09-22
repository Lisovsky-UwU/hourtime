from datetime import date, datetime, time
from typing import Annotated

from pydantic import PlainSerializer


def _serialize_time_no_microseconds(value: time) -> str:
    return value.strftime("%H:%M:%S")

TimeNoMicroseconds = Annotated[time, PlainSerializer(
    _serialize_time_no_microseconds,
    return_type=str,
)]


def get_current_date() -> date:
    return datetime.now().date()

def get_current_time() -> time:
    return datetime.now().time()


DATE_FORMAT_DESC = "Format: YYYY-MM-DD"
DATE_EXAMPLES = ["2025-09-25"]

TIME_FORMAT_DESC = "Format: HH:MM:SS"
TIME_EXAMPLES = ["15:23:01", "14:03"]


