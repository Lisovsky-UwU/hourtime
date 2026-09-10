from datetime import timedelta
from uuid import uuid4

import pytest

from hourtime.domain.errors import NotFound, ValidationError
from hourtime.use_cases.dto import (
    CreateTimeEntryInput,
    ListTimeEntriesInput,
    StartTimerInput,
    StopTimerInput,
    UpdateTimeEntryInput,
)
from hourtime.use_cases.time_entries import (
    CreateTimeEntry,
    DeleteTimeEntry,
    GetRunningTimer,
    ListTimeEntries,
    StartTimer,
    StopTimer,
    UpdateTimeEntry,
)
from tests.factories import make_entry, make_project, make_user
from tests.fakes import (
    FakeClock,
    FakeUnitOfWork,
    InMemoryProjectRepository,
    InMemoryTimeEntryRepository,
)


class TimerWorld:
    def __init__(self) -> None:
        self.clock = FakeClock()
        self.entries = InMemoryTimeEntryRepository()
        self.projects = InMemoryProjectRepository()
        self.uow = FakeUnitOfWork()
        self.user = make_user()
        self.other_user = make_user(email="someone@example.com")

        self.start = StartTimer(self.entries, self.projects, self.clock, self.uow)
        self.stop = StopTimer(self.entries, self.clock, self.uow)
        self.running = GetRunningTimer(self.entries)
        self.listing = ListTimeEntries(self.entries)
        self.create = CreateTimeEntry(self.entries, self.projects, self.clock, self.uow)
        self.update = UpdateTimeEntry(self.entries, self.projects, self.clock, self.uow)
        self.delete = DeleteTimeEntry(self.entries, self.uow)


@pytest.fixture
def world() -> TimerWorld:
    return TimerWorld()


class TestStart:
    async def test_starts_at_now_by_default(self, world: TimerWorld) -> None:
        entry = await world.start.execute(StartTimerInput(user_id=world.user.id))
        assert entry.started_at == world.clock.now()
        assert entry.is_running

    async def test_accepts_a_backdated_start(self, world: TimerWorld) -> None:
        earlier = world.clock.now() - timedelta(hours=2)
        entry = await world.start.execute(
            StartTimerInput(user_id=world.user.id, started_at=earlier)
        )
        assert entry.started_at == earlier

    async def test_rejects_a_start_in_the_future(self, world: TimerWorld) -> None:
        later = world.clock.now() + timedelta(hours=1)
        with pytest.raises(ValidationError):
            await world.start.execute(StartTimerInput(user_id=world.user.id, started_at=later))

    async def test_stops_the_previous_timer(self, world: TimerWorld) -> None:
        first = await world.start.execute(StartTimerInput(user_id=world.user.id))
        world.clock.advance(timedelta(minutes=25))

        second = await world.start.execute(StartTimerInput(user_id=world.user.id))

        closed = await world.entries.get_by_id(first.id)
        assert closed is not None
        assert closed.stopped_at == second.started_at
        assert await world.running.execute(world.user.id) == second

    async def test_backdated_start_closes_the_previous_entry_without_overlap(
        self, world: TimerWorld
    ) -> None:
        first = await world.start.execute(StartTimerInput(user_id=world.user.id))
        world.clock.advance(timedelta(hours=1))
        boundary = world.clock.now() - timedelta(minutes=20)

        second = await world.start.execute(
            StartTimerInput(user_id=world.user.id, started_at=boundary)
        )

        closed = await world.entries.get_by_id(first.id)
        assert closed is not None
        assert closed.stopped_at == boundary == second.started_at

    async def test_rejects_a_start_that_predates_the_running_entry(
        self, world: TimerWorld
    ) -> None:
        await world.start.execute(StartTimerInput(user_id=world.user.id))
        world.clock.advance(timedelta(minutes=10))
        with pytest.raises(ValidationError):
            await world.start.execute(
                StartTimerInput(
                    user_id=world.user.id, started_at=world.clock.now() - timedelta(hours=1)
                )
            )

    async def test_rejects_someone_elses_project(self, world: TimerWorld) -> None:
        theirs = await world.projects.add(make_project(world.other_user.id))
        with pytest.raises(NotFound):
            await world.start.execute(
                StartTimerInput(user_id=world.user.id, project_id=theirs.id)
            )

    async def test_rejects_an_archived_project(self, world: TimerWorld) -> None:
        archived = await world.projects.add(
            make_project(world.user.id, archived_at=world.clock.now())
        )
        with pytest.raises(ValidationError):
            await world.start.execute(
                StartTimerInput(user_id=world.user.id, project_id=archived.id)
            )

    async def test_timers_of_different_users_do_not_interfere(self, world: TimerWorld) -> None:
        mine = await world.start.execute(StartTimerInput(user_id=world.user.id))
        theirs = await world.start.execute(StartTimerInput(user_id=world.other_user.id))
        assert await world.running.execute(world.user.id) == mine
        assert await world.running.execute(world.other_user.id) == theirs


class TestStop:
    async def test_stops_at_now_by_default(self, world: TimerWorld) -> None:
        entry = await world.start.execute(StartTimerInput(user_id=world.user.id))
        world.clock.advance(timedelta(minutes=45))

        stopped = await world.stop.execute(
            StopTimerInput(user_id=world.user.id, entry_id=entry.id)
        )

        assert stopped.stopped_at == world.clock.now()
        assert stopped.duration(world.clock.now()) == timedelta(minutes=45)
        assert await world.running.execute(world.user.id) is None

    async def test_stops_the_current_timer_without_an_id(self, world: TimerWorld) -> None:
        await world.start.execute(StartTimerInput(user_id=world.user.id))
        world.clock.advance(timedelta(minutes=5))
        stopped = await world.stop.execute(StopTimerInput(user_id=world.user.id))
        assert not stopped.is_running

    async def test_complains_when_nothing_runs(self, world: TimerWorld) -> None:
        with pytest.raises(NotFound):
            await world.stop.execute(StopTimerInput(user_id=world.user.id))

    async def test_rejects_stopping_before_the_start(self, world: TimerWorld) -> None:
        entry = await world.start.execute(StartTimerInput(user_id=world.user.id))
        with pytest.raises(ValidationError):
            await world.stop.execute(
                StopTimerInput(
                    user_id=world.user.id,
                    entry_id=entry.id,
                    stopped_at=entry.started_at - timedelta(minutes=1),
                )
            )

    async def test_rejects_stopping_twice(self, world: TimerWorld) -> None:
        entry = await world.start.execute(StartTimerInput(user_id=world.user.id))
        world.clock.advance(timedelta(minutes=5))
        await world.stop.execute(StopTimerInput(user_id=world.user.id, entry_id=entry.id))
        with pytest.raises(ValidationError):
            await world.stop.execute(StopTimerInput(user_id=world.user.id, entry_id=entry.id))


class TestManualEntry:
    async def test_creates_a_finished_entry(self, world: TimerWorld) -> None:
        started = world.clock.now() - timedelta(hours=3)
        stopped = world.clock.now() - timedelta(hours=1)

        entry = await world.create.execute(
            CreateTimeEntryInput(
                user_id=world.user.id,
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
                    started_at=world.clock.now(),
                    stopped_at=world.clock.now() - timedelta(hours=1),
                )
            )


class TestUpdate:
    async def test_changes_comment_project_and_times(self, world: TimerWorld) -> None:
        project = await world.projects.add(make_project(world.user.id))
        entry = await world.entries.add(
            make_entry(world.user.id, started_at=world.clock.now() - timedelta(hours=2))
        )
        new_stop = world.clock.now() - timedelta(minutes=30)

        updated = await world.update.execute(
            UpdateTimeEntryInput(
                user_id=world.user.id,
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
        project = await world.projects.add(make_project(world.user.id))
        entry = await world.entries.add(
            make_entry(world.user.id, project_id=project.id, description="Kept")
        )

        updated = await world.update.execute(
            UpdateTimeEntryInput(user_id=world.user.id, entry_id=entry.id, description="Changed")
        )

        assert updated.project_id == project.id
        assert updated.description == "Changed"

    async def test_explicit_null_detaches_the_project(self, world: TimerWorld) -> None:
        project = await world.projects.add(make_project(world.user.id))
        entry = await world.entries.add(make_entry(world.user.id, project_id=project.id))

        # Passing None explicitly lands in `model_fields_set`, which is how the
        # use case tells "detach the project" from "field not sent".
        updated = await world.update.execute(
            UpdateTimeEntryInput(user_id=world.user.id, entry_id=entry.id, project_id=None)
        )

        assert updated.project_id is None

    async def test_rejects_someone_elses_entry(self, world: TimerWorld) -> None:
        theirs = await world.entries.add(make_entry(world.other_user.id))
        with pytest.raises(NotFound):
            await world.update.execute(
                UpdateTimeEntryInput(
                    user_id=world.user.id, entry_id=theirs.id, description="mine now"
                )
            )

    async def test_rejects_an_inverted_interval(self, world: TimerWorld) -> None:
        entry = await world.entries.add(
            make_entry(world.user.id, started_at=world.clock.now() - timedelta(hours=2))
        )
        with pytest.raises(ValidationError):
            await world.update.execute(
                UpdateTimeEntryInput(
                    user_id=world.user.id,
                    entry_id=entry.id,
                    stopped_at=world.clock.now() - timedelta(hours=3),
                )
            )

    async def test_refuses_to_reopen_an_entry_while_another_runs(
        self, world: TimerWorld
    ) -> None:
        finished = await world.entries.add(
            make_entry(
                world.user.id,
                started_at=world.clock.now() - timedelta(hours=2),
                stopped_at=world.clock.now() - timedelta(hours=1),
            )
        )
        await world.start.execute(StartTimerInput(user_id=world.user.id))

        with pytest.raises(ValidationError):
            await world.update.execute(
                UpdateTimeEntryInput(
                    user_id=world.user.id, entry_id=finished.id, stopped_at=None
                )
            )


class TestListing:
    async def test_orders_newest_first_and_paginates(self, world: TimerWorld) -> None:
        base = world.clock.now() - timedelta(days=1)
        for index in range(5):
            await world.entries.add(
                make_entry(
                    world.user.id,
                    started_at=base + timedelta(hours=index),
                    stopped_at=base + timedelta(hours=index, minutes=30),
                )
            )

        page = await world.listing.execute(
            ListTimeEntriesInput(user_id=world.user.id, limit=2, offset=0)
        )

        assert page.total == 5
        assert len(page.items) == 2
        assert page.items[0].started_at > page.items[1].started_at

    async def test_filters_by_project_and_range(self, world: TimerWorld) -> None:
        project = await world.projects.add(make_project(world.user.id))
        base = world.clock.now() - timedelta(days=2)
        await world.entries.add(
            make_entry(world.user.id, started_at=base, stopped_at=base + timedelta(hours=1))
        )
        await world.entries.add(
            make_entry(
                world.user.id,
                project_id=project.id,
                started_at=base + timedelta(days=1),
                stopped_at=base + timedelta(days=1, hours=1),
            )
        )

        page = await world.listing.execute(
            ListTimeEntriesInput(user_id=world.user.id, project_id=project.id)
        )

        assert page.total == 1
        assert page.items[0].project_id == project.id

    async def test_never_shows_another_users_entries(self, world: TimerWorld) -> None:
        await world.entries.add(make_entry(world.other_user.id))
        page = await world.listing.execute(ListTimeEntriesInput(user_id=world.user.id))
        assert page.total == 0

    async def test_rejects_an_oversized_page(self, world: TimerWorld) -> None:
        with pytest.raises(ValidationError):
            await world.listing.execute(ListTimeEntriesInput(user_id=world.user.id, limit=10_000))


class TestDelete:
    async def test_removes_own_entry(self, world: TimerWorld) -> None:
        entry = await world.entries.add(make_entry(world.user.id))
        await world.delete.execute(world.user.id, entry.id)
        assert await world.entries.get_by_id(entry.id) is None

    async def test_rejects_someone_elses_entry(self, world: TimerWorld) -> None:
        theirs = await world.entries.add(make_entry(world.other_user.id))
        with pytest.raises(NotFound):
            await world.delete.execute(world.user.id, theirs.id)
        assert await world.entries.get_by_id(theirs.id) is not None

    async def test_reports_a_missing_entry_as_not_found(self, world: TimerWorld) -> None:
        with pytest.raises(NotFound):
            await world.delete.execute(world.user.id, uuid4())
