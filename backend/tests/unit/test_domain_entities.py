from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError as PydanticValidationError

from hourtime.domain.entities import normalise_color
from hourtime.domain.errors import ValidationError
from tests.factories import NOW, make_entry, make_project, make_user


class TestColor:
    @pytest.mark.parametrize(
        ("given", "expected"),
        [
            ("#4285F4", "#4285f4"),
            ("4285f4", "#4285f4"),
            ("#ABC", "#aabbcc"),
            ("  #fff  ", "#ffffff"),
        ],
    )
    def test_normalises(self, given: str, expected: str) -> None:
        assert normalise_color(given) == expected

    @pytest.mark.parametrize("given", ["", "#12345", "blue", "#gggggg"])
    def test_rejects_garbage(self, given: str) -> None:
        with pytest.raises(ValidationError):
            make_project(make_user().id, color=given)


class TestProject:
    def test_trims_name(self) -> None:
        assert make_project(make_user().id, name="  Website  ").name == "Website"

    def test_rejects_blank_name(self) -> None:
        with pytest.raises(ValidationError):
            make_project(make_user().id, name="   ")

    def test_archived_flag_follows_timestamp(self) -> None:
        project = make_project(make_user().id)
        assert not project.is_archived
        assert project.evolve(archived_at=NOW).is_archived


class TestTimeEntry:
    def test_running_entry_has_no_stop(self) -> None:
        assert make_entry(make_user().id).is_running

    def test_duration_of_running_entry_uses_now(self) -> None:
        entry = make_entry(make_user().id)
        assert entry.duration(NOW + timedelta(minutes=30)) == timedelta(minutes=30)

    def test_duration_of_stopped_entry_ignores_now(self) -> None:
        entry = make_entry(make_user().id).stop(NOW + timedelta(hours=1))
        assert entry.duration(NOW + timedelta(days=5)) == timedelta(hours=1)

    def test_rejects_stop_before_start(self) -> None:
        with pytest.raises(ValidationError):
            make_entry(make_user().id).stop(NOW - timedelta(seconds=1))

    def test_rejects_naive_datetimes(self) -> None:
        with pytest.raises(ValidationError):
            make_entry(make_user().id, started_at=datetime(2026, 3, 1, 12, 0))

    def test_converts_other_zones_to_utc(self) -> None:
        moscow = datetime(2026, 3, 1, 15, 0, tzinfo=UTC).astimezone()
        entry = make_entry(make_user().id, started_at=moscow)
        assert entry.started_at.tzinfo is UTC

    def test_evolve_revalidates(self) -> None:
        """`model_copy` would skip this check — `evolve` must not."""
        entry = make_entry(make_user().id).stop(NOW + timedelta(hours=1))
        with pytest.raises(ValidationError):
            entry.evolve(started_at=NOW + timedelta(hours=2))


class TestUser:
    def test_folds_email(self) -> None:
        assert make_user(email="  Owner@Example.COM ").email == "owner@example.com"

    def test_rejects_malformed_email(self) -> None:
        with pytest.raises(ValidationError):
            make_user(email="not-an-email")


def test_entity_is_frozen() -> None:
    project = make_project(make_user().id)
    # setattr, not `project.name = ...`, so the type checker does not reject the
    # very assignment this test exists to prove is refused at runtime.
    with pytest.raises(PydanticValidationError):
        setattr(project, "name", "nope")  # noqa: B010
