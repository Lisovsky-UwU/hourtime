"""End-to-end tests over the real stack: FastAPI, SQLAlchemy, Postgres."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import sqlalchemy as sa
from fastapi import FastAPI
from sqlalchemy import event as sa_event

EMAIL = "owner@example.com"
PASSWORD = "correct-horse-battery"


async def register_and_login(client: httpx.AsyncClient) -> dict[str, str]:
    await client.post("/auth/register", json={"email": EMAIL, "password": PASSWORD})
    response = await client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert response.status_code == 200
    tokens = response.json()["tokens"]
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    return dict(tokens)


async def other_user_headers(client: httpx.AsyncClient) -> dict[str, str]:
    """Register a second account and return its auth header; it has its own workspace."""
    await client.post("/auth/register", json={"email": "other@example.com", "password": PASSWORD})
    login = await client.post(
        "/auth/login", json={"email": "other@example.com", "password": PASSWORD}
    )
    return {"Authorization": f"Bearer {login.json()['tokens']['access_token']}"}


async def track(client: httpx.AsyncClient, hours_ago: int, **fields: object) -> dict:
    """A finished half-hour entry, `hours_ago` hours back."""
    started = datetime.now(UTC) - timedelta(hours=hours_ago)
    response = await client.post(
        "/time-entries",
        json={
            "started_at": started.isoformat(),
            "stopped_at": (started + timedelta(minutes=30)).isoformat(),
            **fields,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
async def tokens(client: httpx.AsyncClient) -> dict[str, str]:
    return await register_and_login(client)


@pytest.fixture
def sql_statements(app: FastAPI) -> Iterator[list[str]]:
    """Every statement the API sends, so a test can count them."""
    recorded: list[str] = []

    def record(
        conn: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        recorded.append(statement)

    engine = app.state.engine.sync_engine
    sa_event.listen(engine, "before_cursor_execute", record)
    yield recorded
    sa_event.remove(engine, "before_cursor_execute", record)


class TestAuthEndpoints:
    async def test_register_login_and_me(self, client: httpx.AsyncClient) -> None:
        created = await client.post("/auth/register", json={"email": EMAIL, "password": PASSWORD})
        assert created.status_code == 201
        assert created.json()["email"] == EMAIL

        await register_and_login(client)
        me = await client.get("/auth/me")
        assert me.status_code == 200
        assert me.json()["email"] == EMAIL

    async def test_duplicate_registration_conflicts(self, client: httpx.AsyncClient) -> None:
        await client.post("/auth/register", json={"email": EMAIL, "password": PASSWORD})
        again = await client.post("/auth/register", json={"email": EMAIL, "password": PASSWORD})
        assert again.status_code == 409
        assert again.json()["error"]["code"] == "email_already_used"

    async def test_short_password_is_rejected(self, client: httpx.AsyncClient) -> None:
        response = await client.post("/auth/register", json={"email": EMAIL, "password": "short"})
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "validation_error"

    async def test_protected_routes_need_a_token(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/projects")
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"

    async def test_refresh_rotates_and_retires_the_old_pair(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        rotated = await client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert rotated.status_code == 200
        fresh = rotated.json()["tokens"]
        assert fresh["access_token"] != tokens["access_token"]

        stale = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert stale.status_code == 401

        alive = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {fresh['access_token']}"}
        )
        assert alive.status_code == 200

    async def test_logout_invalidates_immediately(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        """The session cache must not keep a revoked token alive."""
        assert (await client.get("/auth/me")).status_code == 200

        assert (await client.post("/auth/logout")).status_code == 204

        after = await client.get("/auth/me")
        assert after.status_code == 401
        assert after.json()["error"]["code"] == "invalid_token"

    async def test_registration_switch_closes_the_door(
        self, app: FastAPI, client: httpx.AsyncClient
    ) -> None:
        app.state.settings = app.state.settings.model_copy(update={"allow_registration": False})
        response = await client.post("/auth/register", json={"email": EMAIL, "password": PASSWORD})
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "registration_disabled"


class TestProfileEndpoints:
    async def test_defaults_are_reported(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        me = (await client.get("/auth/me")).json()
        assert me["display_name"] is None
        assert me["timezone"] is None
        assert (me["week_start"], me["duration_format"], me["hour_cycle"]) == (1, "classic", 24)

    async def test_patch_is_visible_on_the_next_read(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        """The cached user must be dropped, or other devices keep the old settings."""
        assert (await client.get("/auth/me")).status_code == 200

        patched = await client.patch(
            "/auth/me",
            json={"timezone": "Asia/Yekaterinburg", "duration_format": "decimal", "hour_cycle": 12},
        )
        assert patched.status_code == 200
        assert patched.json()["timezone"] == "Asia/Yekaterinburg"

        me = (await client.get("/auth/me")).json()
        assert me["timezone"] == "Asia/Yekaterinburg"
        assert me["duration_format"] == "decimal"
        assert me["hour_cycle"] == 12

    @pytest.mark.parametrize(
        "body",
        [
            {"timezone": "Nowhere/Town"},
            {"week_start": 7},
            {"hour_cycle": 13},
            {"email": "other@example.com"},
        ],
    )
    async def test_rejects_bad_values(
        self, client: httpx.AsyncClient, tokens: dict[str, str], body: dict[str, object]
    ) -> None:
        response = await client.patch("/auth/me", json=body)
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "validation_error"

    async def test_password_change_keeps_this_device_only(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        other = await client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
        other_headers = {"Authorization": f"Bearer {other.json()['tokens']['access_token']}"}
        assert (await client.get("/auth/me", headers=other_headers)).status_code == 200

        changed = await client.post(
            "/auth/me/password",
            json={"current_password": PASSWORD, "new_password": "new-horse-battery"},
        )
        assert changed.status_code == 204

        assert (await client.get("/auth/me")).status_code == 200
        assert (await client.get("/auth/me", headers=other_headers)).status_code == 401

        old = await client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
        assert old.status_code == 401
        new = await client.post(
            "/auth/login", json={"email": EMAIL, "password": "new-horse-battery"}
        )
        assert new.status_code == 200

    async def test_wrong_current_password_is_not_a_401(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        """A 401 would make the client refresh its tokens instead of showing the error."""
        response = await client.post(
            "/auth/me/password",
            json={"current_password": "not-the-password", "new_password": "new-horse-battery"},
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_current_password"


class TestProjectEndpoints:
    async def test_crud_round_trip(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> None:
        created = await client.post("/projects", json={"name": "Website", "color": "#A1B2C3"})
        assert created.status_code == 201
        project = created.json()
        assert project["color"] == "#a1b2c3"

        listed = await client.get("/projects")
        assert [item["name"] for item in listed.json()] == ["Website"]

        renamed = await client.patch(f"/projects/{project['id']}", json={"name": "Landing"})
        assert renamed.json()["name"] == "Landing"

        archived = await client.patch(f"/projects/{project['id']}", json={"archived": True})
        assert archived.json()["archived"] is True
        assert await (await client.get("/projects")).aread() == b"[]"

        with_archived = await client.get("/projects", params={"include_archived": True})
        assert len(with_archived.json()) == 1

        assert (await client.delete(f"/projects/{project['id']}")).status_code == 204
        assert (await client.get("/projects", params={"include_archived": True})).json() == []

    async def test_duplicate_name_conflicts(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        await client.post("/projects", json={"name": "Website"})
        again = await client.post("/projects", json={"name": "website"})
        assert again.status_code == 409
        assert again.json()["error"]["code"] == "project_name_taken"

    async def test_invalid_colour_is_rejected(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        response = await client.post("/projects", json={"name": "Website", "color": "teal"})
        assert response.status_code == 400


class TestTimerEndpoints:
    async def test_start_stop_and_list(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        project = (await client.post("/projects", json={"name": "Website"})).json()

        started = await client.post(
            "/time-entries/start",
            json={"project_id": project["id"], "description": "Landing page"},
        )
        assert started.status_code == 201
        entry = started.json()
        assert entry["stopped_at"] is None
        assert entry["duration_seconds"] is None

        current = await client.get("/time-entries/current")
        assert current.json()["id"] == entry["id"]

        stopped = await client.post(f"/time-entries/{entry['id']}/stop", json={})
        assert stopped.status_code == 200
        assert stopped.json()["duration_seconds"] >= 0

        assert (await client.get("/time-entries/current")).json() is None

        page = await client.get("/time-entries")
        assert len(page.json()["items"]) == 1

    async def test_survives_a_reload(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        """The running timer lives on the server, so a fresh client still sees it."""
        started = (await client.post("/time-entries/start", json={})).json()

        second_device = await client.post(
            "/auth/login", json={"email": EMAIL, "password": PASSWORD}
        )
        other_token = second_device.json()["tokens"]["access_token"]
        seen = await client.get(
            "/time-entries/current", headers={"Authorization": f"Bearer {other_token}"}
        )
        assert seen.json()["id"] == started["id"]

    async def test_starting_again_closes_the_previous_entry(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        first = (await client.post("/time-entries/start", json={})).json()
        second = (await client.post("/time-entries/start", json={})).json()

        page = (await client.get("/time-entries")).json()
        assert len(page["items"]) == 2
        closed = next(item for item in page["items"] if item["id"] == first["id"])
        assert closed["stopped_at"] is not None
        assert (await client.get("/time-entries/current")).json()["id"] == second["id"]

    async def test_backdated_start(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> None:
        earlier = datetime.now(UTC) - timedelta(hours=2)
        entry = (
            await client.post("/time-entries/start", json={"started_at": earlier.isoformat()})
        ).json()
        assert datetime.fromisoformat(entry["started_at"]) == earlier

    async def test_future_start_is_rejected(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        later = datetime.now(UTC) + timedelta(hours=1)
        response = await client.post(
            "/time-entries/start", json={"started_at": later.isoformat()}
        )
        assert response.status_code == 400

    async def test_naive_timestamps_are_rejected(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        response = await client.post(
            "/time-entries/start", json={"started_at": "2026-03-01T12:00:00"}
        )
        assert response.status_code == 400

    async def test_edit_and_delete_an_entry(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        project = (await client.post("/projects", json={"name": "Website"})).json()
        started = datetime.now(UTC) - timedelta(hours=3)
        stopped = datetime.now(UTC) - timedelta(hours=1)
        entry = (
            await client.post(
                "/time-entries",
                json={"started_at": started.isoformat(), "stopped_at": stopped.isoformat()},
            )
        ).json()
        assert entry["duration_seconds"] == pytest.approx(7200, abs=2)

        edited = await client.patch(
            f"/time-entries/{entry['id']}",
            json={"project_id": project["id"], "description": "Report"},
        )
        assert edited.json()["project_id"] == project["id"]
        assert edited.json()["description"] == "Report"

        detached = await client.patch(f"/time-entries/{entry['id']}", json={"project_id": None})
        assert detached.json()["project_id"] is None

        assert (await client.delete(f"/time-entries/{entry['id']}")).status_code == 204
        assert (await client.get("/time-entries")).json()["items"] == []

    async def test_deleting_a_project_keeps_the_entry(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        project = (await client.post("/projects", json={"name": "Website"})).json()
        entry = (
            await client.post("/time-entries/start", json={"project_id": project["id"]})
        ).json()

        await client.delete(f"/projects/{project['id']}")

        page = (await client.get("/time-entries")).json()
        assert len(page["items"]) == 1
        assert page["items"][0]["id"] == entry["id"]
        assert page["items"][0]["project_id"] is None


class TestSuggestions:
    async def _track(self, client: httpx.AsyncClient, description: str, hours_ago: int, **extra):
        started = datetime.now(UTC) - timedelta(hours=hours_ago)
        response = await client.post(
            "/time-entries",
            json={
                "description": description,
                "started_at": started.isoformat(),
                "stopped_at": (started + timedelta(minutes=30)).isoformat(),
                **extra,
            },
        )
        assert response.status_code == 201

    async def test_pairs_newest_first_without_archived_projects(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        live = (await client.post("/projects", json={"name": "Website"})).json()
        old = (await client.post("/projects", json={"name": "Legacy"})).json()
        await self._track(client, "Ревью кода", 6, project_id=old["id"])
        await self._track(client, "Ревью кода", 5)
        await self._track(client, "Ревью кода", 4, project_id=live["id"])
        await self._track(client, "Ревью кода", 3, project_id=live["id"])
        await self._track(client, "Standup", 2)
        await self._track(client, "", 1)
        await client.patch(f"/projects/{old['id']}", json={"archived": True})

        response = await client.get("/time-entries/suggestions")

        assert response.status_code == 200
        assert [(item["description"], item["project_id"]) for item in response.json()] == [
            ("Standup", None),
            ("Ревью кода", live["id"]),
            ("Ревью кода", None),
        ]

    async def test_search_ignores_case_and_wildcards(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        await self._track(client, "Ревью кода", 3)
        await self._track(client, "Discount 100%", 2)
        await self._track(client, "Discount 1000", 1)

        cyrillic = await client.get("/time-entries/suggestions", params={"q": "РЕВЬЮ"})
        assert [item["description"] for item in cyrillic.json()] == ["Ревью кода"]

        literal = await client.get("/time-entries/suggestions", params={"q": "0%"})
        assert [item["description"] for item in literal.json()] == ["Discount 100%"]

        underscore = await client.get("/time-entries/suggestions", params={"q": "1_0"})
        assert underscore.json() == []

    async def test_limit_is_bounded(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        response = await client.get("/time-entries/suggestions", params={"limit": 500})
        assert response.status_code == 400


class TestClientEndpoints:
    async def test_crud_round_trip(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> None:
        created = await client.post("/clients", json={"name": "  Globex "})
        assert created.status_code == 201
        globex = created.json()
        assert (globex["name"], globex["archived"]) == ("Globex", False)
        await client.post("/clients", json={"name": "acme"})

        listed = await client.get("/clients")
        assert [item["name"] for item in listed.json()] == ["acme", "Globex"]

        renamed = await client.patch(f"/clients/{globex['id']}", json={"name": "Initech"})
        assert renamed.json()["name"] == "Initech"

        archived = await client.patch(f"/clients/{globex['id']}", json={"archived": True})
        assert archived.json()["archived"] is True
        assert [item["name"] for item in (await client.get("/clients")).json()] == ["acme"]
        everything = await client.get("/clients", params={"include_archived": True})
        assert len(everything.json()) == 2

        assert (await client.delete(f"/clients/{globex['id']}")).status_code == 204
        assert len((await client.get("/clients", params={"include_archived": True})).json()) == 1

    async def test_duplicate_name_conflicts_until_archived(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        first = (await client.post("/clients", json={"name": "Acme"})).json()
        again = await client.post("/clients", json={"name": "ACME"})
        assert again.status_code == 409
        assert again.json()["error"]["code"] == "client_name_taken"

        await client.patch(f"/clients/{first['id']}", json={"archived": True})
        assert (await client.post("/clients", json={"name": "Acme"})).status_code == 201

    async def test_another_workspaces_client_looks_missing(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        mine = (await client.post("/clients", json={"name": "Acme"})).json()
        other = await other_user_headers(client)

        assert (await client.get("/clients", headers=other)).json() == []
        patched = await client.patch(f"/clients/{mine['id']}", json={"name": "X"}, headers=other)
        assert patched.status_code == 404
        assert (await client.delete(f"/clients/{mine['id']}", headers=other)).status_code == 404
        borrowed = await client.post(
            "/projects", json={"name": "Website", "client_id": mine["id"]}, headers=other
        )
        assert borrowed.status_code == 404

    async def test_projects_get_and_lose_a_client(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        acme = (await client.post("/clients", json={"name": "Acme"})).json()
        project = (
            await client.post("/projects", json={"name": "Website", "client_id": acme["id"]})
        ).json()
        assert project["client_id"] == acme["id"]

        renamed = await client.patch(f"/projects/{project['id']}", json={"name": "Landing"})
        assert renamed.json()["client_id"] == acme["id"]

        detached = await client.patch(f"/projects/{project['id']}", json={"client_id": None})
        assert detached.json()["client_id"] is None

        reattached = await client.patch(
            f"/projects/{project['id']}", json={"client_id": acme["id"]}
        )
        assert reattached.json()["client_id"] == acme["id"]

    async def test_an_archived_client_cannot_be_assigned(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        acme = (await client.post("/clients", json={"name": "Acme"})).json()
        await client.patch(f"/clients/{acme['id']}", json={"archived": True})

        response = await client.post("/projects", json={"name": "Website", "client_id": acme["id"]})
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "validation_error"

    async def test_deleting_a_client_keeps_its_projects(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        acme = (await client.post("/clients", json={"name": "Acme"})).json()
        project = (
            await client.post("/projects", json={"name": "Website", "client_id": acme["id"]})
        ).json()

        assert (await client.delete(f"/clients/{acme['id']}")).status_code == 204

        projects = (await client.get("/projects")).json()
        assert [(item["id"], item["client_id"]) for item in projects] == [(project["id"], None)]


class TestTagEndpoints:
    async def test_crud_round_trip(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> None:
        created = await client.post("/tags", json={"name": " urgent "})
        assert created.status_code == 201
        urgent = created.json()
        assert urgent["name"] == "urgent"
        await client.post("/tags", json={"name": "Billable"})

        assert [item["name"] for item in (await client.get("/tags")).json()] == [
            "Billable",
            "urgent",
        ]

        renamed = await client.patch(f"/tags/{urgent['id']}", json={"name": "asap"})
        assert renamed.json()["name"] == "asap"

        assert (await client.delete(f"/tags/{urgent['id']}")).status_code == 204
        assert [item["name"] for item in (await client.get("/tags")).json()] == ["Billable"]

    async def test_duplicate_name_conflicts(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        await client.post("/tags", json={"name": "billable"})
        again = await client.post("/tags", json={"name": "BILLABLE"})
        assert again.status_code == 409
        assert again.json()["error"]["code"] == "tag_name_taken"

    async def test_rename_needs_a_name(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        tag = (await client.post("/tags", json={"name": "billable"})).json()
        assert (await client.patch(f"/tags/{tag['id']}", json={})).status_code == 400

    async def test_another_workspaces_tag_looks_missing(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        mine = (await client.post("/tags", json={"name": "billable"})).json()
        other = await other_user_headers(client)

        assert (await client.get("/tags", headers=other)).json() == []
        patched = await client.patch(f"/tags/{mine['id']}", json={"name": "x"}, headers=other)
        assert patched.status_code == 404
        assert (await client.delete(f"/tags/{mine['id']}", headers=other)).status_code == 404
        borrowed = await client.post(
            "/time-entries/start", json={"tag_ids": [mine["id"]]}, headers=other
        )
        assert borrowed.status_code == 404


class TestEntryTags:
    async def test_tags_travel_through_the_timer(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        red = (await client.post("/tags", json={"name": "red"})).json()
        blue = (await client.post("/tags", json={"name": "blue"})).json()
        expected = sorted([red["id"], blue["id"]])

        started = await client.post(
            "/time-entries/start", json={"tag_ids": [red["id"], blue["id"], red["id"]]}
        )
        assert started.status_code == 201
        entry = started.json()
        assert entry["tag_ids"] == expected

        assert (await client.get("/time-entries/current")).json()["tag_ids"] == expected
        stopped = await client.post(f"/time-entries/{entry['id']}/stop", json={})
        assert stopped.json()["tag_ids"] == expected
        assert (await client.get("/time-entries")).json()["items"][0]["tag_ids"] == expected

    async def test_untagged_entries_report_an_empty_list(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        entry = await track(client, 1)
        assert entry["tag_ids"] == []

    async def test_patch_keeps_replaces_and_clears(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        red = (await client.post("/tags", json={"name": "red"})).json()
        blue = (await client.post("/tags", json={"name": "blue"})).json()
        entry = await track(client, 1, tag_ids=[red["id"]])

        kept = await client.patch(f"/time-entries/{entry['id']}", json={"description": "x"})
        assert kept.json()["tag_ids"] == [red["id"]]

        replaced = await client.patch(
            f"/time-entries/{entry['id']}", json={"tag_ids": [blue["id"]]}
        )
        assert replaced.json()["tag_ids"] == [blue["id"]]

        cleared = await client.patch(f"/time-entries/{entry['id']}", json={"tag_ids": []})
        assert cleared.json()["tag_ids"] == []
        assert (await client.get("/time-entries")).json()["items"][0]["tag_ids"] == []

        rejected = await client.patch(f"/time-entries/{entry['id']}", json={"tag_ids": None})
        assert rejected.status_code == 400

    async def test_deleting_a_tag_takes_it_off_entries(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        red = (await client.post("/tags", json={"name": "red"})).json()
        blue = (await client.post("/tags", json={"name": "blue"})).json()
        entry = await track(client, 1, tag_ids=[red["id"], blue["id"]])

        assert (await client.delete(f"/tags/{red['id']}")).status_code == 204

        items = (await client.get("/time-entries")).json()["items"]
        assert [(item["id"], item["tag_ids"]) for item in items] == [(entry["id"], [blue["id"]])]

    async def test_list_loads_tags_in_one_query(
        self, client: httpx.AsyncClient, tokens: dict[str, str], sql_statements: list[str]
    ) -> None:
        tag = (await client.post("/tags", json={"name": "red"})).json()
        for hours_ago in range(1, 6):
            await track(client, hours_ago, tag_ids=[tag["id"]])

        sql_statements.clear()
        page = (await client.get("/time-entries")).json()

        assert all(item["tag_ids"] == [tag["id"]] for item in page["items"])
        tag_reads = [item for item in sql_statements if "FROM time_entry_tags" in item]
        assert len(tag_reads) == 1


class TestEntryFilters:
    async def test_by_client(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> None:
        acme = (await client.post("/clients", json={"name": "Acme"})).json()
        billed = (
            await client.post("/projects", json={"name": "Billed", "client_id": acme["id"]})
        ).json()
        internal = (await client.post("/projects", json={"name": "Internal"})).json()
        on_client = await track(client, 3, project_id=billed["id"])
        await track(client, 2, project_id=internal["id"])
        await track(client, 1)

        page = await client.get("/time-entries", params={"client_id": acme["id"]})
        assert [item["id"] for item in page.json()["items"]] == [on_client["id"]]

    async def test_by_tags_matches_any_without_repeating_rows(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        red = (await client.post("/tags", json={"name": "red"})).json()
        blue = (await client.post("/tags", json={"name": "blue"})).json()
        green = (await client.post("/tags", json={"name": "green"})).json()
        both = await track(client, 3, tag_ids=[red["id"], blue["id"]])
        only_blue = await track(client, 2, tag_ids=[blue["id"]])
        await track(client, 1, tag_ids=[green["id"]])
        await track(client, 4)

        page = await client.get(
            "/time-entries", params=[("tag_ids", red["id"]), ("tag_ids", blue["id"])]
        )
        assert [item["id"] for item in page.json()["items"]] == [only_blue["id"], both["id"]]

        first = await client.get(
            "/time-entries",
            params=[("tag_ids", red["id"]), ("tag_ids", blue["id"]), ("limit", 1)],
        )
        assert first.json()["has_more"] is True

    async def test_without_project(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> None:
        project = (await client.post("/projects", json={"name": "Website"})).json()
        await track(client, 2, project_id=project["id"])
        bare = await track(client, 1)

        page = await client.get("/time-entries", params={"without_project": True})
        assert [item["id"] for item in page.json()["items"]] == [bare["id"]]

    async def test_without_project_conflicts_with_a_project_filter(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        project = (await client.post("/projects", json={"name": "Website"})).json()
        response = await client.get(
            "/time-entries", params={"without_project": True, "project_id": project["id"]}
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "validation_error"


class TestIsolationBetweenUsers:
    async def test_another_users_project_looks_missing(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        mine = (await client.post("/projects", json={"name": "Website"})).json()

        await client.post(
            "/auth/register", json={"email": "other@example.com", "password": PASSWORD}
        )
        other_login = await client.post(
            "/auth/login", json={"email": "other@example.com", "password": PASSWORD}
        )
        other_headers = {
            "Authorization": f"Bearer {other_login.json()['tokens']['access_token']}"
        }

        assert (await client.get("/projects", headers=other_headers)).json() == []
        peek = await client.patch(
            f"/projects/{mine['id']}", json={"name": "Stolen"}, headers=other_headers
        )
        assert peek.status_code == 404

    async def test_project_names_repeat_across_workspaces(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        await client.post("/projects", json={"name": "Website"})

        await client.post(
            "/auth/register", json={"email": "other@example.com", "password": PASSWORD}
        )
        other_login = await client.post(
            "/auth/login", json={"email": "other@example.com", "password": PASSWORD}
        )
        other_headers = {
            "Authorization": f"Bearer {other_login.json()['tokens']['access_token']}"
        }

        created = await client.post("/projects", json={"name": "Website"}, headers=other_headers)
        assert created.status_code == 201


class TestSessionCache:
    async def test_repeated_requests_hit_the_database_once(
        self, client: httpx.AsyncClient, tokens: dict[str, str], sql_statements: list[str]
    ) -> None:
        """Authenticating costs one session read and one user read, warm or not.

        Caching only the session would still leave a `FROM users` on every
        request, which is the whole cost this cache exists to remove.
        """
        sql_statements.clear()
        for _ in range(3):
            assert (await client.get("/auth/me")).status_code == 200

        for table in ("sessions", "users"):
            lookups = [item for item in sql_statements if f"FROM {table}" in item]
            assert len(lookups) == 1, f"{table} was read {len(lookups)} times"

    async def test_revocation_beats_the_cache(
        self, client: httpx.AsyncClient, tokens: dict[str, str], sql_statements: list[str]
    ) -> None:
        await client.get("/auth/me")
        await client.post("/auth/logout")

        sql_statements.clear()
        assert (await client.get("/auth/me")).status_code == 401
        # The cached entry was dropped, so this request had to ask Postgres.
        assert any("FROM sessions" in item for item in sql_statements)


class TestDatabaseGuarantees:
    async def test_only_one_entry_can_be_running(
        self, app: FastAPI, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        """The partial unique index, not just the use case, enforces this."""
        for _ in range(3):
            await client.post("/time-entries/start", json={})

        async with app.state.sessionmaker() as session:
            running = await session.execute(
                sa.text("SELECT count(*) FROM time_entries WHERE stopped_at IS NULL")
            )
            assert running.scalar_one() == 1

    async def test_data_lands_in_the_personal_workspace(
        self, app: FastAPI, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        project = (await client.post("/projects", json={"name": "Website"})).json()
        await client.post("/time-entries/start", json={"project_id": project["id"]})

        async with app.state.sessionmaker() as session:
            rows = await session.execute(
                sa.text(
                    """
                    SELECT w.owner_id = u.id AS owned, w.name,
                           p.workspace_id = w.id AS project_in, t.workspace_id = w.id AS entry_in
                    FROM users u
                    JOIN workspaces w ON w.id = u.default_workspace_id
                    JOIN projects p ON p.id = :project_id
                    JOIN time_entries t ON t.user_id = u.id
                    """
                ),
                {"project_id": project["id"]},
            )
            assert rows.one()._asdict() == {
                "owned": True,
                "name": "Personal",
                "project_in": True,
                "entry_in": True,
            }

    async def test_responses_carry_the_server_clock(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/health")
        stamped = datetime.fromisoformat(response.headers["x-server-time"])
        assert abs((datetime.now(UTC) - stamped).total_seconds()) < 5


class TestBilling:
    async def test_workspace_settings_round_trip(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        fresh = await client.get("/workspaces/current")
        assert fresh.status_code == 200
        assert fresh.json()["default_hourly_rate"] is None
        assert fresh.json()["currency"] == "USD"

        updated = await client.patch(
            "/workspaces/current", json={"default_hourly_rate": 1500.5, "currency": "rub"}
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["default_hourly_rate"] == "1500.50"
        assert updated.json()["currency"] == "RUB"

        cleared = await client.patch("/workspaces/current", json={"default_hourly_rate": None})
        assert cleared.json()["default_hourly_rate"] is None
        assert (await client.get("/workspaces/current")).json()["currency"] == "RUB"

    @pytest.mark.parametrize(
        "body",
        [
            {"currency": "R$"},
            {"currency": None},
            {"default_hourly_rate": -1},
            {"default_hourly_rate": "10.555"},
            {"name": "Team"},
        ],
    )
    async def test_rejects_bad_workspace_settings(
        self, client: httpx.AsyncClient, tokens: dict[str, str], body: dict[str, object]
    ) -> None:
        response = await client.patch("/workspaces/current", json=body)
        assert response.status_code == 400, response.text

    async def test_each_user_sees_their_own_workspace(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        await client.patch("/workspaces/current", json={"currency": "EUR"})
        other = await other_user_headers(client)
        theirs = await client.get("/workspaces/current", headers=other)
        assert theirs.json()["currency"] == "USD"

    async def test_project_rate_is_stored_to_the_cent(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        created = await client.post(
            "/projects", json={"name": "Website", "billable": True, "hourly_rate": "150"}
        )
        assert created.status_code == 201, created.text
        assert created.json()["billable"] is True
        assert created.json()["hourly_rate"] == "150.00"

        listed = (await client.get("/projects")).json()
        assert listed[0]["hourly_rate"] == "150.00"

        cleared = await client.patch(
            f"/projects/{created.json()['id']}", json={"hourly_rate": None}
        )
        assert cleared.json()["hourly_rate"] is None
        assert cleared.json()["billable"] is True

    async def test_entries_follow_the_project_default(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        paid = (await client.post("/projects", json={"name": "Paid", "billable": True})).json()
        free = (await client.post("/projects", json={"name": "Free"})).json()

        started = await client.post("/time-entries/start", json={"project_id": paid["id"]})
        assert started.json()["billable"] is True

        moved = await client.patch(
            f"/time-entries/{started.json()['id']}", json={"project_id": free["id"]}
        )
        assert moved.json()["billable"] is False

        toggled = await client.patch(
            f"/time-entries/{started.json()['id']}", json={"billable": True}
        )
        assert toggled.json()["billable"] is True

        manual = await track(client, 3, project_id=paid["id"], billable=False)
        assert manual["billable"] is False

        listed = (await client.get("/time-entries")).json()["items"]
        assert {item["id"]: item["billable"] for item in listed} == {
            started.json()["id"]: True,
            manual["id"]: False,
        }
