from datetime import timedelta
from decimal import Decimal

import pytest

from hourtime.domain.billing import billable_amount, effective_rate
from hourtime.domain.errors import NotFound, ValidationError
from hourtime.use_cases.dto import UpdateWorkspaceInput
from hourtime.use_cases.workspaces import GetWorkspace, UpdateWorkspace
from tests.factories import make_project, make_user, make_workspace
from tests.fakes import FakeClock, FakeUnitOfWork, InMemoryWorkspaceRepository


class TestEffectiveRate:
    def test_the_project_rate_wins(self) -> None:
        assert effective_rate(Decimal("150.00"), Decimal("100.00")) == Decimal("150.00")

    def test_a_zero_project_rate_still_wins(self) -> None:
        # Zero is a deliberate "this project is free", not "no rate".
        assert effective_rate(Decimal("0.00"), Decimal("100.00")) == Decimal("0.00")

    def test_falls_back_to_the_workspace_rate(self) -> None:
        assert effective_rate(None, Decimal("100.00")) == Decimal("100.00")

    def test_no_rate_anywhere(self) -> None:
        assert effective_rate(None, None) is None


class TestBillableAmount:
    @pytest.mark.parametrize(
        ("duration", "rate", "expected"),
        [
            (timedelta(hours=1), "100.00", "100.00"),
            (timedelta(minutes=90), "33.33", "50.00"),  # 49.995 rounds up
            (timedelta(seconds=18), "1.00", "0.01"),  # 0.005 rounds up
            (timedelta(seconds=17), "1.00", "0.00"),
            (timedelta(minutes=20), "1500.00", "500.00"),
            (timedelta(hours=1), "0.00", "0.00"),
        ],
    )
    def test_rounds_half_up_to_the_cent(
        self, duration: timedelta, rate: str, expected: str
    ) -> None:
        assert billable_amount(duration, Decimal(rate)) == Decimal(expected)

    def test_ignores_fractions_of_a_second(self) -> None:
        duration = timedelta(hours=1, microseconds=999_999)
        assert billable_amount(duration, Decimal("100.00")) == Decimal("100.00")


class TestRateAndCurrencyRules:
    def test_rates_are_kept_to_the_cent(self) -> None:
        project = make_project(make_user().default_workspace_id, hourly_rate="150")
        assert project.hourly_rate == Decimal("150.00")
        assert str(project.hourly_rate) == "150.00"

    @pytest.mark.parametrize("rate", ["-1", "10.555", "10000000000.00"])
    def test_rejects_bad_rates(self, rate: str) -> None:
        with pytest.raises(ValidationError):
            make_project(make_user().default_workspace_id, hourly_rate=rate)

    def test_currency_defaults_to_usd(self) -> None:
        assert make_workspace(make_user()).currency == "USD"

    def test_currency_is_folded_to_upper_case(self) -> None:
        assert make_workspace(make_user(), currency=" rub ").currency == "RUB"

    @pytest.mark.parametrize("currency", ["", "RU", "RUBL", "R1B"])
    def test_rejects_bad_currency_codes(self, currency: str) -> None:
        with pytest.raises(ValidationError):
            make_workspace(make_user(), currency=currency)


class WorkspaceWorld:
    def __init__(self) -> None:
        self.clock = FakeClock()
        self.uow = FakeUnitOfWork()
        self.user = make_user()
        self.workspaces = InMemoryWorkspaceRepository([make_workspace(self.user)])

        self.get = GetWorkspace(self.workspaces)
        self.update = UpdateWorkspace(self.workspaces, self.clock, self.uow)


@pytest.fixture
def world() -> WorkspaceWorld:
    return WorkspaceWorld()


class TestWorkspaceSettings:
    async def test_reads_the_workspace(self, world: WorkspaceWorld) -> None:
        workspace = await world.get.execute(world.user.default_workspace_id)
        assert (workspace.default_hourly_rate, workspace.currency) == (None, "USD")

    async def test_reports_a_missing_workspace(self, world: WorkspaceWorld) -> None:
        with pytest.raises(NotFound):
            await world.get.execute(make_user().default_workspace_id)

    async def test_sets_rate_and_currency(self, world: WorkspaceWorld) -> None:
        world.clock.advance(timedelta(minutes=5))
        updated = await world.update.execute(
            UpdateWorkspaceInput(
                workspace_id=world.user.default_workspace_id,
                default_hourly_rate=Decimal("1500"),
                currency="rub",
            )
        )
        assert updated.default_hourly_rate == Decimal("1500.00")
        assert updated.currency == "RUB"
        assert updated.updated_at == world.clock.now()
        assert world.uow.commits == 1

    async def test_null_removes_the_rate(self, world: WorkspaceWorld) -> None:
        workspace_id = world.user.default_workspace_id
        await world.update.execute(
            UpdateWorkspaceInput(workspace_id=workspace_id, default_hourly_rate=Decimal("10"))
        )
        updated = await world.update.execute(
            UpdateWorkspaceInput(workspace_id=workspace_id, default_hourly_rate=None)
        )
        assert updated.default_hourly_rate is None

    async def test_currency_cannot_be_null(self, world: WorkspaceWorld) -> None:
        with pytest.raises(ValidationError):
            await world.update.execute(
                UpdateWorkspaceInput(workspace_id=world.user.default_workspace_id, currency=None)
            )

    async def test_rejects_an_unknown_shape_of_currency(self, world: WorkspaceWorld) -> None:
        with pytest.raises(ValidationError):
            await world.update.execute(
                UpdateWorkspaceInput(workspace_id=world.user.default_workspace_id, currency="R$")
            )

    async def test_nothing_sent_changes_nothing(self, world: WorkspaceWorld) -> None:
        await world.update.execute(
            UpdateWorkspaceInput(workspace_id=world.user.default_workspace_id)
        )
        assert world.uow.commits == 0
