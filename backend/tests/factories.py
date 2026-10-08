"""Small builders that keep the tests focused on what they actually assert."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from hourtime.domain.entities import Project, TimeEntry, User

NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)


def make_user(
    *, email: str = "owner@example.com", password_hash: str = "hashed:secret", **overrides: object
) -> User:
    values: dict[str, object] = {
        "id": uuid4(),
        "email": email,
        "password_hash": password_hash,
        "is_active": True,
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return User.model_validate(values)


def make_project(user_id: UUID, *, name: str = "Website", **overrides: object) -> Project:
    values: dict[str, object] = {
        "id": uuid4(),
        "user_id": user_id,
        "name": name,
        "color": "#4285f4",
        "archived_at": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return Project(**values)


def make_entry(user_id: UUID, *, started_at: datetime = NOW, **overrides: object) -> TimeEntry:
    values: dict[str, object] = {
        "id": uuid4(),
        "user_id": user_id,
        "project_id": None,
        "description": "",
        "started_at": started_at,
        "stopped_at": None,
        "created_at": started_at,
        "updated_at": started_at,
    }
    values.update(overrides)
    return TimeEntry(**values)
