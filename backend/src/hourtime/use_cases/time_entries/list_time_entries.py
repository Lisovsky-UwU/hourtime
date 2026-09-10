from hourtime.domain.errors import ValidationError
from hourtime.interfaces.repositories import TimeEntryRepository
from hourtime.use_cases.dto import ListTimeEntriesInput, TimeEntryPage

MAX_LIMIT = 200


class ListTimeEntries:
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

        items = await self._entries.list_for_user(
            data.user_id,
            started_from=data.started_from,
            started_to=data.started_to,
            project_id=data.project_id,
            limit=data.limit,
            offset=data.offset,
        )
        total = await self._entries.count_for_user(
            data.user_id,
            started_from=data.started_from,
            started_to=data.started_to,
            project_id=data.project_id,
        )
        return TimeEntryPage(items=items, total=total, limit=data.limit, offset=data.offset)
