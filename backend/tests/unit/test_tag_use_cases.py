from datetime import timedelta
from uuid import uuid4

import pytest

from hourtime.domain.errors import NotFound, TagNameTaken, ValidationError
from hourtime.use_cases.dto import CreateTagInput, UpdateTagInput
from hourtime.use_cases.tags import CreateTag, DeleteTag, ListTags, UpdateTag
from tests.factories import make_tag, make_user
from tests.fakes import FakeClock, FakeUnitOfWork, InMemoryTagRepository


class TagWorld:
    def __init__(self) -> None:
        self.clock = FakeClock()
        self.tags = InMemoryTagRepository()
        self.uow = FakeUnitOfWork()
        self.workspace_id = make_user().default_workspace_id
        self.other_workspace_id = make_user(email="someone@example.com").default_workspace_id

        self.create = CreateTag(self.tags, self.clock, self.uow)
        self.listing = ListTags(self.tags)
        self.update = UpdateTag(self.tags, self.clock, self.uow)
        self.delete = DeleteTag(self.tags, self.uow)


@pytest.fixture
def world() -> TagWorld:
    return TagWorld()


class TestCreate:
    async def test_strips_the_name(self, world: TagWorld) -> None:
        tag = await world.create.execute(
            CreateTagInput(workspace_id=world.workspace_id, name="  billable ")
        )
        assert tag.name == "billable"
        assert world.uow.commits == 1

    async def test_rejects_a_blank_name(self, world: TagWorld) -> None:
        with pytest.raises(ValidationError):
            await world.create.execute(CreateTagInput(workspace_id=world.workspace_id, name=" "))

    async def test_rejects_a_duplicate_name_ignoring_case(self, world: TagWorld) -> None:
        await world.create.execute(CreateTagInput(workspace_id=world.workspace_id, name="billable"))
        with pytest.raises(TagNameTaken):
            await world.create.execute(
                CreateTagInput(workspace_id=world.workspace_id, name="Billable")
            )

    async def test_the_same_name_is_free_in_another_workspace(self, world: TagWorld) -> None:
        await world.create.execute(CreateTagInput(workspace_id=world.workspace_id, name="billable"))
        theirs = await world.create.execute(
            CreateTagInput(workspace_id=world.other_workspace_id, name="billable")
        )
        assert theirs.workspace_id == world.other_workspace_id


class TestUpdate:
    async def test_renames(self, world: TagWorld) -> None:
        tag = await world.tags.add(make_tag(world.workspace_id))
        later = world.clock.advance(timedelta(minutes=5))
        updated = await world.update.execute(
            UpdateTagInput(workspace_id=world.workspace_id, tag_id=tag.id, name=" urgent ")
        )
        assert (updated.name, updated.updated_at) == ("urgent", later)

    async def test_rejects_a_name_another_tag_holds(self, world: TagWorld) -> None:
        await world.tags.add(make_tag(world.workspace_id, name="billable"))
        other = await world.tags.add(make_tag(world.workspace_id, name="urgent"))
        with pytest.raises(TagNameTaken):
            await world.update.execute(
                UpdateTagInput(workspace_id=world.workspace_id, tag_id=other.id, name="BILLABLE")
            )

    async def test_keeping_its_own_name_is_not_a_clash(self, world: TagWorld) -> None:
        tag = await world.tags.add(make_tag(world.workspace_id, name="billable"))
        updated = await world.update.execute(
            UpdateTagInput(workspace_id=world.workspace_id, tag_id=tag.id, name="Billable")
        )
        assert updated.name == "Billable"

    async def test_rejects_a_tag_from_another_workspace(self, world: TagWorld) -> None:
        theirs = await world.tags.add(make_tag(world.other_workspace_id))
        with pytest.raises(NotFound):
            await world.update.execute(
                UpdateTagInput(workspace_id=world.workspace_id, tag_id=theirs.id, name="mine")
            )


class TestListing:
    async def test_sorts_by_name_within_the_workspace(self, world: TagWorld) -> None:
        await world.tags.add(make_tag(world.workspace_id, name="urgent"))
        await world.tags.add(make_tag(world.workspace_id, name="Billable"))
        await world.tags.add(make_tag(world.other_workspace_id, name="theirs"))

        found = await world.listing.execute(world.workspace_id)
        assert [tag.name for tag in found] == ["Billable", "urgent"]


class TestDelete:
    async def test_removes_the_tag(self, world: TagWorld) -> None:
        tag = await world.tags.add(make_tag(world.workspace_id))
        await world.delete.execute(world.workspace_id, tag.id)
        assert await world.tags.get_by_id(tag.id) is None

    async def test_rejects_a_tag_from_another_workspace(self, world: TagWorld) -> None:
        theirs = await world.tags.add(make_tag(world.other_workspace_id))
        with pytest.raises(NotFound):
            await world.delete.execute(world.workspace_id, theirs.id)
        assert await world.tags.get_by_id(theirs.id) is not None

    async def test_reports_a_missing_tag_as_not_found(self, world: TagWorld) -> None:
        with pytest.raises(NotFound):
            await world.delete.execute(world.workspace_id, uuid4())
