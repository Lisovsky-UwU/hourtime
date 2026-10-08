"""Money rules: which rate applies to an entry and what its time is worth.

Amounts are never stored. They are worked out from the current rates whenever
they are needed, so changing a rate reprices past entries too. The frontend
repeats `billable_amount` in integer cents for its live totals; keep the two
in step.
"""

import re
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import AfterValidator, Field

CENT = Decimal("0.01")
SECONDS_PER_HOUR = 3600

_CURRENCY_CODE = re.compile(r"^[A-Z]{3}$")

DEFAULT_CURRENCY = "USD"


def _to_cents(value: Decimal) -> Decimal:
    # 150 and 150.00 are the same rate; make them read the same before and after storage.
    return value.quantize(CENT)


# Fits the `numeric(12,2)` columns it is stored in.
HourlyRate = Annotated[
    Decimal, Field(ge=0, max_digits=12, decimal_places=2), AfterValidator(_to_cents)
]


def normalise_currency(value: str) -> str:
    """An ISO 4217 code such as USD or RUB; case does not matter on input."""
    code = value.strip().upper()
    if not _CURRENCY_CODE.match(code):
        raise ValueError("must be a three-letter ISO 4217 code such as USD")
    return code


def effective_rate(project_rate: Decimal | None, default_rate: Decimal | None) -> Decimal | None:
    """The project's own rate wins; without one the workspace default applies."""
    return project_rate if project_rate is not None else default_rate


def billable_amount(duration: timedelta, rate: Decimal) -> Decimal:
    """Worth of one entry, rounded half up to the cent. Totals add up these rounded amounts."""
    seconds = Decimal(int(duration.total_seconds()))
    return (seconds * rate / SECONDS_PER_HOUR).quantize(CENT, rounding=ROUND_HALF_UP)
