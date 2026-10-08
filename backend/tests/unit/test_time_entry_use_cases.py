from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from hourtime.domain.errors import NotFound, ValidationError
from hourtime.use_cases.dto import (
    CreateTimeEntryInput,
    ListTimeEntriesInput,
    StartTimerInput,
    StopTimerInput,
    SuggestTimeEntriesInput,
    UpdateTimeEntryInput,
)
from hourtime.use_cases.time_entries import (
    CreateTimeEntry,
    DeleteTimeEntry,
    GetRunningTimer,
    ListTimeEntries,
    StartTimer,
    StopTimer,
    SuggestTimeEntries,
    UpdateTimeEntry,
)
from tests.factories import make_client, make_entry, make_project, make_tag, make_user
from tests.fakes import (
    FakeClock,
    FakeUnitOfWork,
    InMemoryProjectRepository,
    InMemoryTagRepository,
    InMemoryTimeEntryRepository,
)


class TimerWorld:
    def __init__(self) -> None:
        self.clock = FakeClock()
        self.projects = InMemoryProjectRepository()
        self.entries = InMemoryTimeEntryRepository(projects=self.projects)
        self.tags = InMemoryTagRepository()
        self.uow = FakeUnitOfWork()
        self.user = make_user()
        self.other_user = make_user(email="someone@example.com")

        self.start = StartTimer(self.entries, self.projects, self.tags, self.clock, self.uow)
        self.stop = StopTimer(self.entries, self.clock, self.uow)
        self.running = GetRunningTimer(self.entries)
        self.listing = ListTimeEntries(self.entries)
        self.create = CreateTimeEntry(self.entries, self.projects, self.tags, self.clock, self.uow)
        self.update = UpdateTimeEntry(self.entries, self.projects, self.tags, self.clock, self.uow)
        self.delete = DeleteTimeEntry(self.entries, self.uow)
        self.suggest = SuggestTimeEntries(self.entries)


@pytest.fixture
def world() -> TimerWorld:
    return TimerWorld()


class TestStart:
    async def test_starts_at_now_by_default(self, world: TimerWorld) -> None:
        entry = await world.start.execute(
            StartTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
        )
        assert entry.started_at == world.clock.now()
        assert entry.is_running

    async def test_accepts_a_backdated_start(self, world: TimerWorld) -> None:
        earlier = world.clock.now() - timedelta(hours=2)
        entry = await world.start.execute(
            StartTimerInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                started_at=earlier,
            )
        )
        assert entry.started_at == earlier

    async def test_rejects_a_start_in_the_future(self, world: TimerWorld) -> None:
        later = world.clock.now() + timedelta(hours=1)
        with pytest.raises(ValidationError):
            await world.start.execute(
                StartTimerInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    started_at=later,
                )
            )

    async def test_stops_the_previous_timer(self, world: TimerWorld) -> None:
        first = await world.start.execute(
            StartTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
        )
        world.clock.advance(timedelta(minutes=25))

        second = await world.start.execute(
            StartTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
        )

        closed = await world.entries.get_by_id(first.id)
        assert closed is not None
        assert closed.stopped_at == second.started_at
        assert await world.running.execute(world.user.id) == second

    async def test_backdated_start_closes_the_previous_entry_without_overlap(
        self, world: TimerWorld
    ) -> None:
        first = await world.start.execute(
            StartTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
        )
        world.clock.advance(timedelta(hours=1))
        boundary = world.clock.now() - timedelta(minutes=20)

        second = await world.start.execute(
            StartTimerInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                started_at=boundary,
            )
        )

        closed = await world.entries.get_by_id(first.id)
        assert closed is not None
        assert closed.stopped_at == boundary == second.started_at

    async def test_rejects_a_start_that_predates_the_running_entry(self, world: TimerWorld) -> None:
        await world.start.execute(
            StartTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
        )
        world.clock.advance(timedelta(minutes=10))
        with pytest.raises(ValidationError):
            await world.start.execute(
                StartTimerInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    started_at=world.clock.now() - timedelta(hours=1),
                )
            )

    async def test_rejects_someone_elses_project(self, world: TimerWorld) -> None:
        theirs = await world.projects.add(make_project(world.other_user.default_workspace_id))
        with pytest.raises(NotFound):
            await world.start.execute(
                StartTimerInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    project_id=theirs.id,
                )
            )

    async def test_rejects_an_archived_project(self, world: TimerWorld) -> None:
        archived = await world.projects.add(
            make_project(world.user.default_workspace_id, archived_at=world.clock.now())
        )
        with pytest.raises(ValidationError):
            await world.start.execute(
                StartTimerInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    project_id=archived.id,
                )
            )

    async def test_timers_of_different_users_do_not_interfere(self, world: TimerWorld) -> None:
        mine = await world.start.execute(
            StartTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
        )
        theirs = await world.start.execute(
            StartTimerInput(
                user_id=world.other_user.id, workspace_id=world.other_user.default_workspace_id
            )
        )
        assert await world.running.execute(world.user.id) == mine
        assert await world.running.execute(world.other_user.id) == theirs


class TestStop:
    async def test_stops_at_now_by_default(self, world: TimerWorld) -> None:
        entry = await world.start.execute(
            StartTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
        )
        world.clock.advance(timedelta(minutes=45))

        stopped = await world.stop.execute(
            StopTimerInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                entry_id=entry.id,
            )
        )

        assert stopped.stopped_at == world.clock.now()
        assert stopped.duration(world.clock.now()) == timedelta(minutes=45)
        assert await world.running.execute(world.user.id) is None

    async def test_stops_the_current_timer_without_an_id(self, world: TimerWorld) -> None:
        await world.start.execute(
            StartTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
        )
        world.clock.advance(timedelta(minutes=5))
        stopped = await world.stop.execute(
            StopTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
        )
        assert not stopped.is_running

    async def test_complains_when_nothing_runs(self, world: TimerWorld) -> None:
        with pytest.raises(NotFound):
            await world.stop.execute(
                StopTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
            )

    async def test_rejects_stopping_before_the_start(self, world: TimerWorld) -> None:
        entry = await world.start.execute(
            StartTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
        )
        with pytest.raises(ValidationError):
            await world.stop.execute(
                StopTimerInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    entry_id=entry.id,
                    stopped_at=entry.started_at - timedelta(minutes=1),
                )
            )

    async def test_rejects_stopping_twice(self, world: TimerWorld) -> None:
        entry = await world.start.execute(
            StartTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
        )
        world.clock.advance(timedelta(minutes=5))
        await world.stop.execute(
            StopTimerInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                entry_id=entry.id,
            )
        )
        with pytest.raises(ValidationError):
            await world.stop.execute(
                StopTimerInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    entry_id=entry.id,
                )
            )


class TestManualEntry:
    async def test_creates_a_finished_entry(self, world: TimerWorld) -> None:
        started = world.clock.now() - timedelta(hours=3)
        stopped = world.clock.now() - timedelta(hours=1)

        entry = await world.create.execute(
            CreateTimeEntryInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                started_at=started,
                stopped_at=stopped,
                description="  Wrote the report  ",
            )
        )

        assert entry.duration(world.clock.now()) == timedelta(hours=2)
        assert entry.description == "Wrote the report"

    async def test_rejects_inverted_interval(self, world: TimerWorld) -> None:
        with pytest.raises(ValidationError):
            await world.create.execute(
                CreateTimeEntryInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    started_at=world.clock.now(),
                    stopped_at=world.clock.now() - timedelta(hours=1),
                )
            )


class TestUpdate:
    async def test_changes_comment_project_and_times(self, world: TimerWorld) -> None:
        project = await world.projects.add(make_project(world.user.default_workspace_id))
        entry = await world.entries.add(
            make_entry(world.user, started_at=world.clock.now() - timedelta(hours=2))
        )
        new_stop = world.clock.now() - timedelta(minutes=30)

        updated = await world.update.execute(
            UpdateTimeEntryInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                entry_id=entry.id,
                project_id=project.id,
                description="Refactoring",
                stopped_at=new_stop,
            )
        )

        assert updated.project_id == project.id
        assert updated.description == "Refactoring"
        assert updated.stopped_at == new_stop

    async def test_omitted_fields_are_untouched(self, world: TimerWorld) -> None:
        project = await world.projects.add(make_project(world.user.default_workspace_id))
        entry = await world.entries.add(
            make_entry(world.user, project_id=project.id, description="Kept")
        )

        updated = await world.update.execute(
            UpdateTimeEntryInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                entry_id=entry.id,
                description="Changed",
            )
        )

        assert updated.project_id == project.id
        assert updated.description == "Changed"

    async def test_explicit_null_detaches_the_project(self, world: TimerWorld) -> None:
        project = await world.projects.add(make_project(world.user.default_workspace_id))
        entry = await world.entries.add(make_entry(world.user, project_id=project.id))

        # Passing None explicitly lands in `model_fields_set`, which is how the
        # use case tells "detach the project" from "field not sent".
        updated = await world.update.execute(
            UpdateTimeEntryInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                entry_id=entry.id,
                project_id=None,
            )
        )

        assert updated.project_id is None

    async def test_rejects_someone_elses_entry(self, world: TimerWorld) -> None:
        theirs = await world.entries.add(make_entry(world.other_user))
        with pytest.raises(NotFound):
            await world.update.execute(
                UpdateTimeEntryInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    entry_id=theirs.id,
                    description="mine now",
                )
            )

    async def test_rejects_an_inverted_interval(self, world: TimerWorld) -> None:
        entry = await world.entries.add(
            make_entry(world.user, started_at=world.clock.now() - timedelta(hours=2))
        )
        with pytest.raises(ValidationError):
            await world.update.execute(
                UpdateTimeEntryInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    entry_id=entry.id,
                    stopped_at=world.clock.now() - timedelta(hours=3),
                )
            )

    async def test_refuses_to_reopen_an_entry_while_another_runs(self, world: TimerWorld) -> None:
        finished = await world.entries.add(
            make_entry(
                world.user,
                started_at=world.clock.now() - timedelta(hours=2),
                stopped_at=world.clock.now() - timedelta(hours=1),
            )
        )
        await world.start.execute(
            StartTimerInput(user_id=world.user.id, workspace_id=world.user.default_workspace_id)
        )

        with pytest.raises(ValidationError):
            await world.update.execute(
                UpdateTimeEntryInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    entry_id=finished.id,
                    stopped_at=None,
                )
            )


class TestListing:
    async def test_orders_newest_first_and_paginates(self, world: TimerWorld) -> None:
        base = world.clock.now() - timedelta(days=1)
        for index in range(5):
            await world.entries.add(
                make_entry(
                    world.user,
                    started_at=base + timedelta(hours=index),
                    stopped_at=base + timedelta(hours=index, minutes=30),
                )
            )

        page = await world.listing.execute(
            ListTimeEntriesInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                limit=2,
                offset=0,
            )
        )

        assert len(page.items) == 2
        assert page.has_more
        assert page.items[0].started_at > page.items[1].started_at

    async def test_last_page_reports_no_more(self, world: TimerWorld) -> None:
        base = world.clock.now() - timedelta(days=1)
        for index in range(3):
            await world.entries.add(
                make_entry(
                    world.user,
                    started_at=base + timedelta(hours=index),
                    stopped_at=base + timedelta(hours=index, minutes=30),
                )
            )

        page = await world.listing.execute(
            ListTimeEntriesInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                limit=3,
                offset=0,
            )
        )

        # Exactly a full page and nothing beyond it.
        assert len(page.items) == 3
        assert not page.has_more

    async def test_filters_by_project_and_range(self, world: TimerWorld) -> None:
        project = await world.projects.add(make_project(world.user.default_workspace_id))
        base = world.clock.now() - timedelta(days=2)
        await world.entries.add(
            make_entry(world.user, started_at=base, stopped_at=base + timedelta(hours=1))
        )
        await world.entries.add(
            make_entry(
                world.user,
                project_id=project.id,
                started_at=base + timedelta(days=1),
                stopped_at=base + timedelta(days=1, hours=1),
            )
        )

        page = await world.listing.execute(
            ListTimeEntriesInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                project_id=project.id,
            )
        )

        assert len(page.items) == 1
        assert page.items[0].project_id == project.id

    async def test_never_shows_another_users_entries(self, world: TimerWorld) -> None:
        await world.entries.add(make_entry(world.other_user))
        page = await world.listing.execute(
            ListTimeEntriesInput(
                user_id=world.user.id, workspace_id=world.user.default_workspace_id
            )
        )
        assert page.items == []
        assert not page.has_more

    async def test_rejects_an_oversized_page(self, world: TimerWorld) -> None:
        with pytest.raises(ValidationError):
            await world.listing.execute(
                ListTimeEntriesInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    limit=10_000,
                )
            )


class TestSuggestions:
    async def _track(self, world: TimerWorld, description: str, hours_ago: int, **extra: object):
        start = world.clock.now() - timedelta(hours=hours_ago)
        return await world.entries.add(
            make_entry(
                world.user,
                description=description,
                started_at=start,
                stopped_at=start + timedelta(minutes=30),
                **extra,
            )
        )

    async def test_distinct_pairs_newest_first(self, world: TimerWorld) -> None:
        project = await world.projects.add(make_project(world.user.default_workspace_id))
        await self._track(world, "Code review", hours_ago=5)
        await self._track(world, "Standup", hours_ago=4)
        await self._track(world, "Code review", hours_ago=3)
        await self._track(world, "Code review", hours_ago=2, project_id=project.id)
        await self._track(world, "", hours_ago=1)

        found = await world.suggest.execute(
            SuggestTimeEntriesInput(
                user_id=world.user.id, workspace_id=world.user.default_workspace_id
            )
        )

        assert [(item.description, item.project_id) for item in found] == [
            ("Code review", project.id),
            ("Code review", None),
            ("Standup", None),
        ]
        assert found[1].last_used_at == world.clock.now() - timedelta(hours=3)

    async def test_matches_any_part_ignoring_case(self, world: TimerWorld) -> None:
        await self._track(world, "Fix login redirect", hours_ago=2)
        await self._track(world, "Standup", hours_ago=1)

        found = await world.suggest.execute(
            SuggestTimeEntriesInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                query="  LOGIN ",
            )
        )

        assert [item.description for item in found] == ["Fix login redirect"]

    async def test_respects_the_limit(self, world: TimerWorld) -> None:
        for index in range(5):
            await self._track(world, f"Task {index}", hours_ago=index + 1)

        found = await world.suggest.execute(
            SuggestTimeEntriesInput(
                user_id=world.user.id, workspace_id=world.user.default_workspace_id, limit=2
            )
        )

        assert [item.description for item in found] == ["Task 0", "Task 1"]

    async def test_never_suggests_another_users_entries(self, world: TimerWorld) -> None:
        await world.entries.add(make_entry(world.other_user, description="Secret"))
        found = await world.suggest.execute(
            SuggestTimeEntriesInput(
                user_id=world.user.id, workspace_id=world.user.default_workspace_id
            )
        )
        assert found == []

    async def test_rejects_an_oversized_limit(self, world: TimerWorld) -> None:
        with pytest.raises(ValidationError):
            await world.suggest.execute(
                SuggestTimeEntriesInput(
                    user_id=world.user.id, workspace_id=world.user.default_workspace_id, limit=1_000
                )
            )


class TestDelete:
    async def test_removes_own_entry(self, world: TimerWorld) -> None:
        entry = await world.entries.add(make_entry(world.user))
        await world.delete.execute(world.user.id, world.user.default_workspace_id, entry.id)
        assert await world.entries.get_by_id(entry.id) is None

    async def test_rejects_someone_elses_entry(self, world: TimerWorld) -> None:
        theirs = await world.entries.add(make_entry(world.other_user))
        with pytest.raises(NotFound):
            await world.delete.execute(world.user.id, world.user.default_workspace_id, theirs.id)
        assert await world.entries.get_by_id(theirs.id) is not None

    async def test_reports_a_missing_entry_as_not_found(self, world: TimerWorld) -> None:
        with pytest.raises(NotFound):
            await world.delete.execute(world.user.id, world.user.default_workspace_id, uuid4())


class TestTags:
    async def test_start_collapses_repeated_tags(self, world: TimerWorld) -> None:
        workspace_id = world.user.default_workspace_id
        first = await world.tags.add(make_tag(workspace_id, name="billable"))
        second = await world.tags.add(make_tag(workspace_id, name="urgent"))

        entry = await world.start.execute(
            StartTimerInput(
                user_id=world.user.id,
                workspace_id=workspace_id,
                tag_ids=[second.id, first.id, second.id],
            )
        )

        assert entry.tag_ids == sorted([first.id, second.id])

    async def test_manual_entry_carries_tags(self, world: TimerWorld) -> None:
        tag = await world.tags.add(make_tag(world.user.default_workspace_id))
        entry = await world.create.execute(
            CreateTimeEntryInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                tag_ids=[tag.id],
                started_at=world.clock.now() - timedelta(hours=2),
                stopped_at=world.clock.now() - timedelta(hours=1),
            )
        )
        assert entry.tag_ids == [tag.id]

    async def test_rejects_a_tag_from_another_workspace(self, world: TimerWorld) -> None:
        mine = await world.tags.add(make_tag(world.user.default_workspace_id))
        theirs = await world.tags.add(make_tag(world.other_user.default_workspace_id))
        with pytest.raises(NotFound):
            await world.start.execute(
                StartTimerInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    tag_ids=[mine.id, theirs.id],
                )
            )
        with pytest.raises(NotFound):
            await world.create.execute(
                CreateTimeEntryInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    tag_ids=[theirs.id],
                    started_at=world.clock.now() - timedelta(hours=2),
                    stopped_at=world.clock.now() - timedelta(hours=1),
                )
            )
        entry = await world.entries.add(make_entry(world.user))
        with pytest.raises(NotFound):
            await world.update.execute(
                UpdateTimeEntryInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    entry_id=entry.id,
                    tag_ids=[theirs.id],
                )
            )

    async def test_rejects_a_missing_tag(self, world: TimerWorld) -> None:
        with pytest.raises(NotFound):
            await world.start.execute(
                StartTimerInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    tag_ids=[uuid4()],
                )
            )

    async def test_patch_without_tag_ids_keeps_them(self, world: TimerWorld) -> None:
        tag = await world.tags.add(make_tag(world.user.default_workspace_id))
        entry = await world.entries.add(make_entry(world.user, tag_ids=[tag.id]))

        updated = await world.update.execute(
            UpdateTimeEntryInput(
                user_id=world.user.id,
                workspace_id=world.user.default_workspace_id,
                entry_id=entry.id,
                description="Changed",
            )
        )

        assert updated.tag_ids == [tag.id]

    async def test_patch_replaces_and_clears_tags(self, world: TimerWorld) -> None:
        workspace_id = world.user.default_workspace_id
        old = await world.tags.add(make_tag(workspace_id, name="old"))
        new = await world.tags.add(make_tag(workspace_id, name="new"))
        entry = await world.entries.add(make_entry(world.user, tag_ids=[old.id]))

        replaced = await world.update.execute(
            UpdateTimeEntryInput(
                user_id=world.user.id,
                workspace_id=workspace_id,
                entry_id=entry.id,
                tag_ids=[new.id, new.id],
            )
        )
        assert replaced.tag_ids == [new.id]

        cleared = await world.update.execute(
            UpdateTimeEntryInput(
                user_id=world.user.id, workspace_id=workspace_id, entry_id=entry.id, tag_ids=[]
            )
        )
        assert cleared.tag_ids == []

    async def test_patch_rejects_null_tag_ids(self, world: TimerWorld) -> None:
        entry = await world.entries.add(make_entry(world.user))
        with pytest.raises(ValidationError):
            await world.update.execute(
                UpdateTimeEntryInput(
                    user_id=world.user.id,
                    workspace_id=world.user.default_workspace_id,
                    entry_id=entry.id,
                    tag_ids=None,
                )
            )


class TestListingFilters:
    async def _track(self, world: TimerWorld, hours_ago: int, **extra: object) -> UUID:
        started = world.clock.now() - timedelta(hours=hours_ago)
        entry = await world.entries.add(
            make_entry(
                world.user, started_at=started, stopped_at=started + timedelta(minutes=30), **extra
            )
        )
        return entry.id

    def _query(self, world: TimerWorld, **filters: Any) -> ListTimeEntriesInput:
        return ListTimeEntriesInput(
            user_id=world.user.id, workspace_id=world.user.default_workspace_id, **filters
        )

    async def test_filters_by_client_tags_and_missing_project(self, world: TimerWorld) -> None:
        workspace_id = world.user.default_workspace_id
        client = make_client(workspace_id)
        billed = await world.projects.add(
            make_project(workspace_id, name="Billed", client_id=client.id)
        )
        internal = await world.projects.add(make_project(workspace_id, name="Internal"))
        red = await world.tags.add(make_tag(workspace_id, name="red"))
        blue = await world.tags.add(make_tag(workspace_id, name="blue"))

        on_client = await self._track(world, 4, project_id=billed.id)
        await self._track(world, 3, project_id=internal.id, tag_ids=[red.id])
        both_tags = await self._track(world, 2, tag_ids=[red.id, blue.id])
        bare = await self._track(world, 1)

        by_client = await world.listing.execute(self._query(world, client_id=client.id))
        assert [entry.id for entry in by_client.items] == [on_client]

        by_tag = await world.listing.execute(self._query(world, tag_ids=[blue.id]))
        assert [entry.id for entry in by_tag.items] == [both_tags]

        no_project = await world.listing.execute(self._query(world, without_project=True))
        assert [entry.id for entry in no_project.items] == [bare, both_tags]

    @pytest.mark.parametrize("other_filter", ["project_id", "client_id"])
    async def test_without_project_conflicts_with_project_filters(
        self, world: TimerWorld, other_filter: str
    ) -> None:
        with pytest.raises(ValidationError):
            await world.listing.execute(
                self._query(world, without_project=True, **{other_filter: uuid4()})
            )
