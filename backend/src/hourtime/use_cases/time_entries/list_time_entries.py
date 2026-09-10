from hourtime.domain.errors import ValidationError
from hourtime.interfaces.repositories import TimeEntryRepository
from hourtime.use_cases.dto import ListTimeEntriesInput, TimeEntryPage

MAX_LIMIT = 200


class ListTimeEntries:
    """One query per page.

    Asking for `limit + 1` rows and dropping the extra tells us whether another
    page exists — a `count(*)` would double the cost of the most-loaded endpoint
    in the app just to render a number nobody acts on.
    """

    def __init__(self, entries: TimeEntryRepository) -> None:
        self._entries = entries

    async def execute(self, data: ListTimeEntriesInput) -> TimeEntryPage:
        if data.limit < 1 or data.limit > MAX_LIMIT:
            raise ValidationError(f"limit must be between 1 and {MAX_LIMIT}")
        if data.offset < 0:
            raise ValidationError("offset cannot be negative")
        if (
            data.started_from is not None
            and data.started_to is not None
            and data.started_from > data.started_to
        ):
            raise ValidationError("started_from must not be later than started_to")

        found = await self._entries.list_for_user(
            data.user_id,
            started_from=data.started_from,
            started_to=data.started_to,
            project_id=data.project_id,
            limit=data.limit + 1,
            offset=data.offset,
        )

        has_more = len(found) > data.limit
        return TimeEntryPage(
            items=found[: data.limit],
            has_more=has_more,
            limit=data.limit,
            offset=data.offset,
        )
