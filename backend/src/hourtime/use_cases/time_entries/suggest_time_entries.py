from hourtime.domain.entities import TimeEntrySuggestion
from hourtime.domain.errors import ValidationError
from hourtime.interfaces.repositories import TimeEntryRepository
from hourtime.use_cases.dto import SuggestTimeEntriesInput

MAX_LIMIT = 50


class SuggestTimeEntries:
    """Autocomplete for the timer's description: what was tracked before, newest first."""

    def __init__(self, entries: TimeEntryRepository) -> None:
        self._entries = entries

    async def execute(self, data: SuggestTimeEntriesInput) -> list[TimeEntrySuggestion]:
        if data.limit < 1 or data.limit > MAX_LIMIT:
            raise ValidationError(f"limit must be between 1 and {MAX_LIMIT}")
        return await self._entries.suggest(data.user_id, query=data.query.strip(), limit=data.limit)
