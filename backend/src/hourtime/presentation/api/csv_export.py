"""Reports as CSV files: comma-separated, dot decimals, UTF-8 with a BOM.

The BOM is what makes Excel read the file as UTF-8 instead of the system code
page. Headers are in English and values are not localised, so scripts and
spreadsheets read every file the same way.
"""

import csv
import io
from collections.abc import AsyncIterator, Iterable, Iterator
from datetime import date
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi.responses import StreamingResponse

from hourtime.domain.reports import GroupKey, ReportEntry, ReportGrouping
from hourtime.use_cases.dto import DetailedExport, SummaryReport

BOM = "﻿"

# A spreadsheet runs a cell that starts like a formula. Descriptions and names
# are typed by people, so such text is written with a leading apostrophe.
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")

GROUP_HEADERS: dict[ReportGrouping, str] = {
    "project": "Project",
    "client": "Client",
    "tag": "Tag",
    "description": "Description",
}

UNNAMED_GROUPS: dict[ReportGrouping, str] = {
    "project": "Without project",
    "client": "Without client",
    "tag": "Without tags",
    "description": "Without description",
}


def _text(value: str) -> str:
    return f"'{value}" if value.startswith(FORMULA_START) else value


def _line(values: Iterable[str]) -> str:
    buffer = io.StringIO()
    csv.writer(buffer).writerow(values)
    return buffer.getvalue()


def _duration(seconds: int) -> str:
    """`H:MM:SS`, hours not wrapped at a day: `37:05:00`."""
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02}:{secs:02}"


def _hours(seconds: int) -> str:
    return f"{Decimal(seconds) / 3600:.2f}"


def _amount(amount: Decimal | None) -> str:
    return "" if amount is None else f"{amount:.2f}"


def _group_name(key: GroupKey, grouping: ReportGrouping) -> str:
    return _text(key.name) if key.name else UNNAMED_GROUPS[grouping]


def _entry_row(entry: ReportEntry, zone: ZoneInfo) -> list[str]:
    started = entry.started_at.astimezone(zone)
    stopped = entry.stopped_at.astimezone(zone)
    return [
        _text(entry.description),
        _text(entry.project.name) if entry.project else "",
        _text(entry.client.name) if entry.client else "",
        ", ".join(_text(tag.name) for tag in entry.tags),
        "Yes" if entry.billable else "No",
        started.date().isoformat(),
        started.strftime("%H:%M:%S"),
        stopped.date().isoformat(),
        stopped.strftime("%H:%M:%S"),
        _duration(entry.duration),
        _hours(entry.duration),
        _amount(entry.amount),
    ]


async def detailed_csv(export: DetailedExport) -> AsyncIterator[str]:
    zone = ZoneInfo(export.timezone)
    yield BOM + _line(
        [
            "Description",
            "Project",
            "Client",
            "Tags",
            "Billable",
            "Start date",
            "Start time",
            "End date",
            "End time",
            "Duration",
            "Duration (hours)",
            f"Amount ({export.currency})",
        ]
    )
    async for page in export.pages:
        yield "".join(_line(_entry_row(entry, zone)) for entry in page)


def summary_csv(
    report: SummaryReport, group_by: ReportGrouping, subgroup_by: ReportGrouping | None
) -> Iterator[str]:
    """One row per group, or per subgroup with its group repeated when split.

    Only the leaves are written, so a column adds up to the report's total
    (except by tag, where an entry with two tags counts under both).
    """
    with_client = group_by == "project"
    header = [GROUP_HEADERS[group_by]]
    if with_client:
        header.append("Client")
    if subgroup_by is not None:
        header.append(GROUP_HEADERS[subgroup_by])
    header += ["Duration", "Duration (hours)", "Billable duration", f"Amount ({report.currency})"]
    yield BOM + _line(header)

    for group in report.groups:
        lead = [_group_name(group.key, group_by)]
        if with_client:
            lead.append(_text(group.key.client_name or ""))
        leaves = (
            [
                (subgroup.totals, [_group_name(subgroup.key, subgroup_by)])
                for subgroup in group.subgroups
            ]
            if subgroup_by is not None
            else [(group.totals, [])]
        )
        for totals, sub in leaves:
            yield _line(
                [
                    *lead,
                    *sub,
                    _duration(totals.duration),
                    _hours(totals.duration),
                    _duration(totals.billable_duration),
                    _amount(totals.amount),
                ]
            )


def csv_response(
    content: AsyncIterator[str] | Iterator[str], kind: str, start: date | None, end: date | None
) -> StreamingResponse:
    period = f"{start.isoformat()}_{end.isoformat()}" if start and end else "all-time"
    return StreamingResponse(
        content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="hourtime-{kind}-{period}.csv"'},
    )
