"""Reports over the real stack: the aggregates are SQL, so they are tested on Postgres."""

import csv
import io
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
import pytest

from hourtime.domain.billing import billable_amount
from tests.integration.test_api_flow import other_user_headers, register_and_login

# 2025-02-03 is a Monday; no DST change anywhere near it in the zones used here.
WEEK = {"start_date": "2025-02-03", "end_date": "2025-02-09"}


@pytest.fixture
async def tokens(client: httpx.AsyncClient) -> dict[str, str]:
    return await register_and_login(client)


async def add(
    client: httpx.AsyncClient, started_at: str, stopped_at: str, **fields: object
) -> dict:
    """A finished entry between two UTC instants written as `2025-02-03T09:00`."""
    response = await client.post(
        "/time-entries",
        json={"started_at": f"{started_at}:00Z", "stopped_at": f"{stopped_at}:00Z", **fields},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def make(client: httpx.AsyncClient, path: str, **body: object) -> dict:
    response = await client.post(path, json=body)
    assert response.status_code == 201, response.text
    return response.json()


async def set_timezone(client: httpx.AsyncClient, timezone: str) -> None:
    response = await client.patch("/auth/me", json={"timezone": timezone})
    assert response.status_code == 200, response.text


async def report(client: httpx.AsyncClient, kind: str, params: Any = None) -> dict:
    response = await client.get(f"/reports/{kind}", params=params)
    assert response.status_code == 200, response.text
    return response.json()


async def detailed_ids(client: httpx.AsyncClient, params: Any = None) -> set[str]:
    return {item["id"] for item in (await report(client, "detailed", params))["items"]}


def by_day(summary: dict) -> dict[str, int]:
    return {day["date"]: day["duration"] for day in summary["by_day"]}


def totals_without_days(totals: dict) -> dict:
    return {key: value for key, value in totals.items() if key != "days"}


class TestDays:
    async def test_entry_across_midnight_belongs_to_its_start_day(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        await add(client, "2025-02-03T23:00", "2025-02-04T01:00")

        summary = await report(client, "summary", WEEK)
        assert by_day(summary)["2025-02-03"] == 7200
        assert by_day(summary)["2025-02-04"] == 0

        weekly = await report(client, "weekly", WEEK)
        assert weekly["totals"]["days"] == [7200, 0, 0, 0, 0, 0, 0]

        # A report for the second day alone does not see it at all.
        only_tuesday = {"start_date": "2025-02-04", "end_date": "2025-02-04"}
        assert (await report(client, "summary", only_tuesday))["totals"]["entries"] == 0

    @pytest.mark.parametrize(
        ("timezone", "day"),
        [
            # 20:00 UTC is 03:00 next morning in Novosibirsk (UTC+7)...
            ("Asia/Novosibirsk", "2025-02-04"),
            # ...and noon of the same day in Los Angeles (UTC-8).
            ("America/Los_Angeles", "2025-02-03"),
            ("UTC", "2025-02-03"),
            (None, "2025-02-03"),
        ],
    )
    async def test_day_is_taken_in_the_users_zone(
        self,
        client: httpx.AsyncClient,
        tokens: dict[str, str],
        timezone: str | None,
        day: str,
    ) -> None:
        # A fresh account has no zone at all, which reports read as UTC.
        if timezone is not None:
            await set_timezone(client, timezone)
        await add(client, "2025-02-03T20:00", "2025-02-03T21:00")

        summary = await report(client, "summary", WEEK)
        assert [date for date, seconds in by_day(summary).items() if seconds] == [day]

        single = await report(client, "detailed", {"start_date": day, "end_date": day})
        assert single["totals"]["entries"] == 1

    async def test_period_edges_follow_local_midnight(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        await set_timezone(client, "Asia/Novosibirsk")
        # 23:59 and 00:00 local time in Novosibirsk.
        last_minute = await add(client, "2025-02-03T16:59", "2025-02-03T17:00")
        first_minute = await add(client, "2025-02-03T17:00", "2025-02-03T17:01")

        monday = {"start_date": "2025-02-03", "end_date": "2025-02-03"}
        tuesday = {"start_date": "2025-02-04", "end_date": "2025-02-04"}
        assert await detailed_ids(client, monday) == {last_minute["id"]}
        assert await detailed_ids(client, tuesday) == {first_minute["id"]}

        weekly = await report(client, "weekly", WEEK)
        assert weekly["totals"]["days"][:2] == [60, 60]

    async def test_by_day_lists_every_day_and_is_null_without_dates(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        await add(client, "2025-02-05T09:00", "2025-02-05T10:00")

        summary = await report(client, "summary", WEEK)
        assert summary["by_day"] == [
            {
                "date": f"2025-02-0{day}",
                "duration": 3600 if day == 5 else 0,
                "billable_duration": 0,
                "amount": "0.00",
            }
            for day in range(3, 10)
        ]
        assert (await report(client, "summary"))["by_day"] is None


class TestTotalsAgree:
    async def test_summary_detailed_and_weekly_add_up_the_same(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        await client.patch("/workspaces/current", json={"default_hourly_rate": "1000"})
        acme = await make(client, "/clients", name="Acme")
        paid = await make(
            client,
            "/projects",
            name="Paid",
            client_id=acme["id"],
            billable=True,
            hourly_rate="1503.33",
        )
        free = await make(client, "/projects", name="Free")
        red = await make(client, "/tags", name="red")
        blue = await make(client, "/tags", name="blue")

        await add(client, "2025-02-03T09:00", "2025-02-03T10:17", project_id=paid["id"])
        await add(
            client,
            "2025-02-04T23:30",
            "2025-02-05T00:45",
            project_id=paid["id"],
            tag_ids=[red["id"], blue["id"]],
        )
        await add(client, "2025-02-06T08:00", "2025-02-06T08:13", billable=True)
        await add(client, "2025-02-07T12:00", "2025-02-07T13:00", project_id=free["id"])
        # Outside the week: must not count anywhere.
        await add(client, "2025-02-10T09:00", "2025-02-10T10:00", project_id=paid["id"])

        summary = (await report(client, "summary", {**WEEK, "group_by": "tag"}))["totals"]
        detailed = (await report(client, "detailed", WEEK))["totals"]
        weekly = (await report(client, "weekly", WEEK))["totals"]
        weekly_by_client = (await report(client, "weekly", {**WEEK, "group_by": "client"}))[
            "totals"
        ]

        assert summary == detailed == totals_without_days(weekly)
        assert totals_without_days(weekly_by_client) == summary
        assert summary["entries"] == 4
        assert summary["duration"] == (77 + 75 + 13 + 60) * 60
        assert summary["billable_duration"] == (77 + 75 + 13) * 60
        assert sum(weekly["days"]) == summary["duration"]


class TestFilters:
    @pytest.fixture
    async def world(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> dict[str, dict]:
        acme = await make(client, "/clients", name="Acme")
        on_client = await make(client, "/projects", name="Billed", client_id=acme["id"])
        no_client = await make(client, "/projects", name="Internal")
        red = await make(client, "/tags", name="red")
        blue = await make(client, "/tags", name="blue")
        entries = {
            "client_red": await add(
                client,
                "2025-02-03T09:00",
                "2025-02-03T10:00",
                project_id=on_client["id"],
                tag_ids=[red["id"]],
                description="100% done",
                billable=True,
            ),
            "internal_blue": await add(
                client,
                "2025-02-04T09:00",
                "2025-02-04T10:00",
                project_id=no_client["id"],
                tag_ids=[blue["id"]],
                description="100 percent",
            ),
            "bare": await add(
                client, "2025-02-05T09:00", "2025-02-05T10:00", description="Daily_sync"
            ),
            "both_tags": await add(
                client,
                "2025-02-12T09:00",
                "2025-02-12T10:00",
                project_id=no_client["id"],
                tag_ids=[red["id"], blue["id"]],
                description="Dailyxsync",
            ),
        }
        return {
            "acme": acme,
            "on_client": on_client,
            "no_client": no_client,
            "red": red,
            "blue": blue,
            **entries,
        }

    @staticmethod
    def ids(world: dict[str, dict], *names: str) -> set[str]:
        return {world[name]["id"] for name in names}

    async def test_projects(self, client: httpx.AsyncClient, world: dict[str, dict]) -> None:
        on_client = world["on_client"]["id"]
        assert await detailed_ids(client, {"project_ids": on_client}) == self.ids(
            world, "client_red"
        )
        assert await detailed_ids(client, {"without_project": True}) == self.ids(world, "bare")
        both = [("project_ids", on_client), ("without_project", "true")]
        assert await detailed_ids(client, both) == self.ids(world, "client_red", "bare")
        several = [("project_ids", on_client), ("project_ids", world["no_client"]["id"])]
        assert await detailed_ids(client, several) == self.ids(
            world, "client_red", "internal_blue", "both_tags"
        )

    async def test_clients(self, client: httpx.AsyncClient, world: dict[str, dict]) -> None:
        acme = world["acme"]["id"]
        assert await detailed_ids(client, {"client_ids": acme}) == self.ids(world, "client_red")
        assert await detailed_ids(client, {"without_client": True}) == self.ids(
            world, "internal_blue", "bare", "both_tags"
        )
        either = [("client_ids", acme), ("without_client", "true")]
        assert await detailed_ids(client, either) == self.ids(
            world, "client_red", "internal_blue", "bare", "both_tags"
        )

    async def test_tags(self, client: httpx.AsyncClient, world: dict[str, dict]) -> None:
        red, blue = world["red"]["id"], world["blue"]["id"]
        assert await detailed_ids(client, {"tag_ids": red}) == self.ids(
            world, "client_red", "both_tags"
        )
        any_of = [("tag_ids", red), ("tag_ids", blue)]
        page = await report(client, "detailed", any_of)
        # Two matching tags still make one row.
        assert len(page["items"]) == page["totals"]["entries"] == 3
        assert await detailed_ids(client, {"without_tags": True}) == self.ids(world, "bare")
        either = [("tag_ids", blue), ("without_tags", "true")]
        assert await detailed_ids(client, either) == self.ids(
            world, "internal_blue", "bare", "both_tags"
        )

    async def test_billable(self, client: httpx.AsyncClient, world: dict[str, dict]) -> None:
        assert await detailed_ids(client, {"billable": True}) == self.ids(world, "client_red")
        assert await detailed_ids(client, {"billable": False}) == self.ids(
            world, "internal_blue", "bare", "both_tags"
        )

    async def test_description(self, client: httpx.AsyncClient, world: dict[str, dict]) -> None:
        assert await detailed_ids(client, {"description": "100%"}) == self.ids(world, "client_red")
        assert await detailed_ids(client, {"description": "100"}) == self.ids(
            world, "client_red", "internal_blue"
        )
        # `_` is literal too, and the match ignores case.
        assert await detailed_ids(client, {"description": "DAILY_"}) == self.ids(world, "bare")
        assert len(await detailed_ids(client, {"description": ""})) == 4

    async def test_period(self, client: httpx.AsyncClient, world: dict[str, dict]) -> None:
        assert await detailed_ids(client, WEEK) == self.ids(
            world, "client_red", "internal_blue", "bare"
        )

    async def test_filters_combine(self, client: httpx.AsyncClient, world: dict[str, dict]) -> None:
        params = {**WEEK, "without_client": True, "tag_ids": world["blue"]["id"]}
        assert await detailed_ids(client, params) == self.ids(world, "internal_blue")

    async def test_unknown_ids_just_match_nothing(
        self, client: httpx.AsyncClient, world: dict[str, dict]
    ) -> None:
        other = await other_user_headers(client)
        theirs = (await client.post("/projects", json={"name": "Theirs"}, headers=other)).json()
        for name in ("project_ids", "client_ids", "tag_ids"):
            for value in (theirs["id"], "00000000-0000-0000-0000-000000000000"):
                found = await report(client, "summary", {name: value})
                assert found["totals"]["entries"] == 0
                assert found["groups"] == []


class TestSummaryGroups:
    async def test_by_project_with_client_and_archived_projects(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        acme = await make(client, "/clients", name="Acme")
        website = await make(
            client, "/projects", name="Website", color="#2f6f4e", client_id=acme["id"]
        )
        old = await make(client, "/projects", name="Old")
        await add(client, "2025-02-03T09:00", "2025-02-03T11:00", project_id=website["id"])
        await add(client, "2025-02-04T09:00", "2025-02-04T10:00", project_id=old["id"])
        await add(client, "2025-02-05T09:00", "2025-02-05T10:00")
        await client.patch(f"/projects/{old['id']}", json={"archived": True})

        groups = (await report(client, "summary", WEEK))["groups"]
        assert [
            (group["id"], group["name"], group["color"], group["client_name"], group["duration"])
            for group in groups
        ] == [
            (website["id"], "Website", "#2f6f4e", "Acme", 7200),
            (old["id"], "Old", old["color"], None, 3600),
            # Equal duration: the unnamed group goes after the named one.
            (None, None, None, None, 3600),
        ]
        assert all(group["subgroups"] == [] for group in groups)

    async def test_by_client(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> None:
        acme = await make(client, "/clients", name="Acme")
        billed = await make(client, "/projects", name="Billed", client_id=acme["id"])
        internal = await make(client, "/projects", name="Internal")
        await add(client, "2025-02-03T09:00", "2025-02-03T09:30", project_id=billed["id"])
        await add(client, "2025-02-03T10:00", "2025-02-03T11:00", project_id=internal["id"])
        await add(client, "2025-02-03T12:00", "2025-02-03T12:30")

        groups = (await report(client, "summary", {"group_by": "client"}))["groups"]
        assert [
            (group["id"], group["name"], group["color"], group["client_name"], group["entries"])
            for group in groups
        ] == [(None, None, None, None, 2), (acme["id"], "Acme", None, None, 1)]

    async def test_by_tag_counts_an_entry_under_each_tag(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        red = await make(client, "/tags", name="red")
        blue = await make(client, "/tags", name="blue")
        await add(client, "2025-02-03T09:00", "2025-02-03T11:00", tag_ids=[red["id"], blue["id"]])
        await add(client, "2025-02-03T12:00", "2025-02-03T13:00", tag_ids=[red["id"]])
        await add(client, "2025-02-03T14:00", "2025-02-03T14:30")

        summary = await report(client, "summary", {"group_by": "tag"})
        groups = {group["name"]: group for group in summary["groups"]}
        assert groups["red"]["duration"] == 3 * 3600
        assert groups["red"]["id"] == red["id"]
        assert groups["blue"]["duration"] == 2 * 3600
        assert groups[None]["id"] is None
        assert groups[None]["duration"] == 1800
        assert summary["totals"]["duration"] == 3 * 3600 + 1800
        assert sum(group["duration"] for group in summary["groups"]) > summary["totals"]["duration"]

    async def test_by_description(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> None:
        await add(client, "2025-02-03T09:00", "2025-02-03T10:00", description="Standup")
        await add(client, "2025-02-04T09:00", "2025-02-04T10:00", description="Standup")
        await add(client, "2025-02-04T11:00", "2025-02-04T11:30", description="standup")
        await add(client, "2025-02-04T12:00", "2025-02-04T12:30")

        groups = (await report(client, "summary", {"group_by": "description"}))["groups"]
        assert [(group["id"], group["name"], group["entries"]) for group in groups] == [
            (None, "Standup", 2),
            (None, "standup", 1),
            (None, None, 1),
        ]

    async def test_subgroups_split_a_group_without_double_counting_it(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        website = await make(client, "/projects", name="Website")
        red = await make(client, "/tags", name="red")
        blue = await make(client, "/tags", name="blue")
        await add(
            client,
            "2025-02-03T09:00",
            "2025-02-03T10:00",
            project_id=website["id"],
            tag_ids=[red["id"], blue["id"]],
        )
        await add(
            client,
            "2025-02-03T11:00",
            "2025-02-03T11:30",
            project_id=website["id"],
            tag_ids=[red["id"]],
        )
        await add(client, "2025-02-03T12:00", "2025-02-03T12:15", project_id=website["id"])
        await add(client, "2025-02-03T13:00", "2025-02-03T13:10", description="Planning")

        summary = await report(client, "summary", {"subgroup_by": "tag"})
        project, no_project = summary["groups"]
        assert (project["name"], project["duration"], project["entries"]) == ("Website", 6300, 3)
        assert [(sub["name"], sub["duration"]) for sub in project["subgroups"]] == [
            ("red", 5400),
            ("blue", 3600),
            (None, 900),
        ]
        assert set(project["subgroups"][0]) == {
            "id",
            "name",
            "color",
            "client_name",
            "duration",
            "billable_duration",
            "amount",
            "entries",
        }
        assert [(sub["name"], sub["duration"]) for sub in no_project["subgroups"]] == [(None, 600)]

        by_description = await report(
            client, "summary", {"group_by": "tag", "subgroup_by": "description"}
        )
        untagged = next(group for group in by_description["groups"] if group["id"] is None)
        assert [(sub["name"], sub["duration"]) for sub in untagged["subgroups"]] == [
            (None, 900),
            ("Planning", 600),
        ]

    async def test_running_and_foreign_entries_are_left_out(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        mine = await add(client, "2025-02-03T09:00", "2025-02-03T10:00")
        assert (await client.post("/time-entries/start", json={})).status_code == 201
        other = await other_user_headers(client)
        await client.post(
            "/time-entries",
            json={"started_at": "2025-02-03T09:00:00Z", "stopped_at": "2025-02-03T12:00:00Z"},
            headers=other,
        )

        summary = await report(client, "summary")
        assert summary["totals"]["entries"] == 1
        assert summary["totals"]["duration"] == 3600
        assert await detailed_ids(client) == {mine["id"]}
        today = datetime.now().date().isoformat()
        assert (await report(client, "weekly", {"start_date": today, "end_date": today}))[
            "rows"
        ] == []


class TestAmounts:
    async def test_project_rate_then_workspace_rate_then_nothing(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        await client.patch("/workspaces/current", json={"currency": "RUB"})
        own_rate = await make(client, "/projects", name="Own", billable=True, hourly_rate="1800")
        no_rate = await make(client, "/projects", name="Default", billable=True)
        priced = await add(
            client, "2025-02-03T09:00", "2025-02-03T10:00", project_id=own_rate["id"]
        )
        unpriced = await add(
            client, "2025-02-03T11:00", "2025-02-03T12:00", project_id=no_rate["id"]
        )
        unbilled = await add(
            client,
            "2025-02-03T13:00",
            "2025-02-03T14:00",
            project_id=own_rate["id"],
            billable=False,
        )

        before = await report(client, "detailed")
        assert before["currency"] == "RUB"
        amounts = {item["id"]: item["amount"] for item in before["items"]}
        assert amounts == {priced["id"]: "1800.00", unpriced["id"]: None, unbilled["id"]: None}
        assert before["totals"] == {
            "duration": 3 * 3600,
            "billable_duration": 2 * 3600,
            "amount": "1800.00",
            "entries": 3,
        }

        # Rates are not stored with entries: a new default reprices the past.
        await client.patch("/workspaces/current", json={"default_hourly_rate": "600.50"})
        after = await report(client, "detailed")
        amounts = {item["id"]: item["amount"] for item in after["items"]}
        assert amounts[unpriced["id"]] == "600.50"
        assert after["totals"]["amount"] == "2400.50"

    async def test_each_entry_is_rounded_like_billable_amount(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        rate = Decimal("33.33")
        project = await make(client, "/projects", name="P", billable=True, hourly_rate=str(rate))
        start = datetime(2025, 2, 3, 9, 0)
        # Seconds chosen to land on and around half a cent.
        durations = [5400, 18, 17, 1, 59, 3599, 7777, 54]
        for index, seconds in enumerate(durations):
            began = start + timedelta(hours=3 * index)
            response = await client.post(
                "/time-entries",
                json={
                    "started_at": f"{began.isoformat()}Z",
                    "stopped_at": f"{(began + timedelta(seconds=seconds)).isoformat()}Z",
                    "project_id": project["id"],
                },
            )
            assert response.status_code == 201, response.text

        expected = [billable_amount(timedelta(seconds=seconds), rate) for seconds in durations]
        page = await report(client, "detailed", {"sort": "started_at", "order": "asc"})
        assert [Decimal(item["amount"]) for item in page["items"]] == expected
        assert Decimal(page["totals"]["amount"]) == sum(expected)
        summary = await report(client, "summary")
        assert Decimal(summary["totals"]["amount"]) == sum(expected)

    async def test_fractional_seconds_are_dropped(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        await client.patch("/workspaces/current", json={"default_hourly_rate": "3600"})
        await client.post(
            "/time-entries",
            json={
                "started_at": "2025-02-03T09:00:00.000Z",
                "stopped_at": "2025-02-03T09:00:01.999Z",
                "billable": True,
            },
        )
        item = (await report(client, "detailed"))["items"][0]
        assert (item["duration"], item["amount"]) == (1, "1.00")


class TestDetailed:
    async def test_item_shape(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> None:
        acme = await make(client, "/clients", name="Acme")
        project = await make(
            client, "/projects", name="hourtime", color="#2f6f4e", client_id=acme["id"]
        )
        zeta = await make(client, "/tags", name="zeta")
        alpha = await make(client, "/tags", name="Alpha")
        entry = await add(
            client,
            "2025-02-05T09:00",
            "2025-02-05T10:00",
            project_id=project["id"],
            tag_ids=[zeta["id"], alpha["id"]],
            description="Planning",
        )
        bare = await add(client, "2025-02-04T09:00", "2025-02-04T09:01")

        page = await report(client, "detailed")
        assert page == {
            "currency": "USD",
            "totals": {"duration": 3660, "billable_duration": 0, "amount": "0.00", "entries": 2},
            "items": [
                {
                    "id": entry["id"],
                    "description": "Planning",
                    "project": {"id": project["id"], "name": "hourtime", "color": "#2f6f4e"},
                    "client": {"id": acme["id"], "name": "Acme"},
                    "tags": [
                        {"id": alpha["id"], "name": "Alpha"},
                        {"id": zeta["id"], "name": "zeta"},
                    ],
                    "billable": False,
                    "started_at": "2025-02-05T09:00:00Z",
                    "stopped_at": "2025-02-05T10:00:00Z",
                    "duration": 3600,
                    "amount": None,
                },
                {
                    "id": bare["id"],
                    "description": "",
                    "project": None,
                    "client": None,
                    "tags": [],
                    "billable": False,
                    "started_at": "2025-02-04T09:00:00Z",
                    "stopped_at": "2025-02-04T09:01:00Z",
                    "duration": 60,
                    "amount": None,
                },
            ],
            "has_more": False,
            "limit": 50,
            "offset": 0,
        }

    async def test_sorting_and_paging(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        beta = await make(client, "/projects", name="beta")
        alpha = await make(client, "/projects", name="Alpha")
        first = await add(
            client, "2025-02-03T09:00", "2025-02-03T09:30", project_id=beta["id"], description="b"
        )
        second = await add(
            client, "2025-02-04T09:00", "2025-02-04T11:00", project_id=alpha["id"], description="C"
        )
        third = await add(client, "2025-02-05T09:00", "2025-02-05T10:00", description="a")
        fourth = await add(client, "2025-02-06T09:00", "2025-02-06T10:00", description="a")

        async def order(**params: object) -> list[str]:
            return [item["id"] for item in (await report(client, "detailed", params))["items"]]

        newest = [fourth["id"], third["id"], second["id"], first["id"]]
        assert await order() == newest
        assert await order(order="asc") == newest[::-1]
        # Equal durations fall back to the newest first.
        assert await order(sort="duration") == [
            second["id"],
            fourth["id"],
            third["id"],
            first["id"],
        ]
        assert await order(sort="duration", order="asc") == [
            first["id"],
            fourth["id"],
            third["id"],
            second["id"],
        ]
        assert await order(sort="description", order="asc") == [
            fourth["id"],
            third["id"],
            first["id"],
            second["id"],
        ]
        # Without a project sorts last either way.
        assert await order(sort="project", order="asc") == [
            second["id"],
            first["id"],
            fourth["id"],
            third["id"],
        ]
        assert await order(sort="project") == [first["id"], second["id"], fourth["id"], third["id"]]

        page = await report(client, "detailed", {"limit": 3})
        assert (len(page["items"]), page["has_more"], page["totals"]["entries"]) == (3, True, 4)
        rest = await report(client, "detailed", {"limit": 3, "offset": 3})
        assert ([item["id"] for item in rest["items"]], rest["has_more"]) == ([first["id"]], False)
        assert rest["totals"]["entries"] == 4


class TestWeekly:
    async def test_rows_by_project_and_client(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        acme = await make(client, "/clients", name="Acme")
        website = await make(
            client, "/projects", name="Website", color="#2f6f4e", client_id=acme["id"]
        )
        await add(client, "2025-02-03T09:00", "2025-02-03T10:00", project_id=website["id"])
        await add(client, "2025-02-05T09:00", "2025-02-05T11:00", project_id=website["id"])
        await add(client, "2025-02-09T09:00", "2025-02-09T09:30")

        weekly = await report(client, "weekly", WEEK)
        assert weekly["days"] == [f"2025-02-0{day}" for day in range(3, 10)]
        assert weekly["rows"] == [
            {
                "id": website["id"],
                "name": "Website",
                "color": "#2f6f4e",
                "client_name": "Acme",
                "days": [3600, 0, 7200, 0, 0, 0, 0],
                "duration": 10800,
                "billable_duration": 0,
                "amount": "0.00",
                "entries": 2,
            },
            {
                "id": None,
                "name": None,
                "color": None,
                "client_name": None,
                "days": [0, 0, 0, 0, 0, 0, 1800],
                "duration": 1800,
                "billable_duration": 0,
                "amount": "0.00",
                "entries": 1,
            },
        ]
        assert weekly["totals"] == {
            "duration": 12600,
            "billable_duration": 0,
            "amount": "0.00",
            "entries": 3,
            "days": [3600, 0, 7200, 0, 0, 0, 1800],
        }

        by_client = await report(client, "weekly", {**WEEK, "group_by": "client"})
        assert [(row["id"], row["name"], row["color"]) for row in by_client["rows"]] == [
            (acme["id"], "Acme", None),
            (None, None, None),
        ]

    async def test_shorter_period(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> None:
        await add(client, "2025-02-04T09:00", "2025-02-04T10:00")
        weekly = await report(
            client, "weekly", {"start_date": "2025-02-04", "end_date": "2025-02-05"}
        )
        assert weekly["days"] == ["2025-02-04", "2025-02-05"]
        assert weekly["totals"]["days"] == [3600, 0]


async def csv_rows(
    client: httpx.AsyncClient, kind: str, params: Any = None
) -> tuple[httpx.Response, list[list[str]]]:
    response = await client.get(f"/reports/{kind}.csv", params=params)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    # The BOM goes first so Excel reads the file as UTF-8.
    assert response.content.startswith("﻿".encode())
    text = response.content.decode("utf-8-sig")
    return response, list(csv.reader(io.StringIO(text, newline="")))


class TestCsv:
    async def test_detailed(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> None:
        await set_timezone(client, "Europe/Moscow")
        await client.patch("/workspaces/current", json={"default_hourly_rate": "1000"})
        acme = await make(client, "/clients", name="Acme")
        project = await make(
            client, "/projects", name="Сайт", color="#2f6f4e", client_id=acme["id"]
        )
        zeta = await make(client, "/tags", name="zeta")
        alpha = await make(client, "/tags", name="Alpha")
        await add(
            client,
            "2025-02-05T21:30",
            "2025-02-06T00:15",
            project_id=project["id"],
            tag_ids=[zeta["id"], alpha["id"]],
            description='Fix, "quoted" и кириллица',
            billable=True,
        )
        await add(client, "2025-02-04T09:00", "2025-02-04T09:01", description="=1+1")

        response, rows = await csv_rows(client, "detailed", {**WEEK, "sort": "duration"})
        assert response.headers["content-disposition"] == (
            'attachment; filename="hourtime-detailed-2025-02-03_2025-02-09.csv"'
        )
        assert rows == [
            [
                "Description",
                "Project",
                "Client",
                "Tags",
                "Billable",
                "Start date",
                "Start time",
                "End date",
                "End time",
                "Duration",
                "Duration (hours)",
                "Amount (USD)",
            ],
            # Times are in the profile's zone: 21:30 UTC is past midnight in Moscow.
            [
                'Fix, "quoted" и кириллица',
                "Сайт",
                "Acme",
                "Alpha, zeta",
                "Yes",
                "2025-02-06",
                "00:30:00",
                "2025-02-06",
                "03:15:00",
                "2:45:00",
                "2.75",
                "2750.00",
            ],
            # A formula would run in a spreadsheet; the apostrophe keeps it text.
            [
                "'=1+1",
                "",
                "",
                "",
                "No",
                "2025-02-04",
                "12:00:00",
                "2025-02-04",
                "12:01:00",
                "0:01:00",
                "0.02",
                "",
            ],
        ]

    async def test_summary(self, client: httpx.AsyncClient, tokens: dict[str, str]) -> None:
        acme = await make(client, "/clients", name="Acme")
        project = await make(
            client, "/projects", name="hourtime", color="#2f6f4e", client_id=acme["id"]
        )
        await add(
            client,
            "2025-02-03T09:00",
            "2025-02-03T10:00",
            project_id=project["id"],
            description="Planning",
        )
        await add(
            client,
            "2025-02-04T09:00",
            "2025-02-04T09:30",
            project_id=project["id"],
            description="Review",
        )
        await add(client, "2025-02-05T09:00", "2025-02-05T19:00")

        response, rows = await csv_rows(client, "summary")
        assert response.headers["content-disposition"] == (
            'attachment; filename="hourtime-summary-all-time.csv"'
        )
        assert rows == [
            [
                "Project",
                "Client",
                "Duration",
                "Duration (hours)",
                "Billable duration",
                "Amount (USD)",
            ],
            ["Without project", "", "10:00:00", "10.00", "0:00:00", "0.00"],
            ["hourtime", "Acme", "1:30:00", "1.50", "0:00:00", "0.00"],
        ]

        _, split = await csv_rows(
            client, "summary", {"group_by": "client", "subgroup_by": "description"}
        )
        assert split == [
            [
                "Client",
                "Description",
                "Duration",
                "Duration (hours)",
                "Billable duration",
                "Amount (USD)",
            ],
            ["Without client", "Without description", "10:00:00", "10.00", "0:00:00", "0.00"],
            ["Acme", "Planning", "1:00:00", "1.00", "0:00:00", "0.00"],
            ["Acme", "Review", "0:30:00", "0.50", "0:00:00", "0.00"],
        ]

    async def test_bad_parameters_fail_before_the_file(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        for kind, params in (
            ("detailed.csv", {"end_date": "2025-02-03"}),
            ("detailed.csv", {"sort": "amount"}),
            ("summary.csv", {"group_by": "client", "subgroup_by": "client"}),
        ):
            response = await client.get(f"/reports/{kind}", params=params)
            assert response.status_code == 400, response.text
            assert response.json()["error"]["code"] == "validation_error"

    async def test_needs_a_token(self, client: httpx.AsyncClient) -> None:
        for kind in ("summary.csv", "detailed.csv"):
            assert (await client.get(f"/reports/{kind}")).status_code == 401


class TestValidation:
    @pytest.mark.parametrize(
        ("kind", "params"),
        [
            ("summary", {"start_date": "2025-02-03"}),
            ("detailed", {"end_date": "2025-02-03"}),
            ("summary", {"start_date": "2025-02-04", "end_date": "2025-02-03"}),
            ("weekly", {}),
            ("weekly", {"start_date": "2025-02-03"}),
            ("weekly", {"start_date": "2025-02-03", "end_date": "2025-02-10"}),
            ("weekly", {**WEEK, "group_by": "tag"}),
            ("summary", {"group_by": "client", "subgroup_by": "client"}),
            ("summary", {"group_by": "user"}),
            ("summary", {"subgroup_by": "day"}),
            ("detailed", {"sort": "amount"}),
            ("detailed", {"order": "up"}),
            ("detailed", {"limit": 0}),
            ("detailed", {"limit": 201}),
            ("detailed", {"offset": -1}),
            ("summary", {"start_date": "03.02.2025", "end_date": "2025-02-03"}),
            ("summary", {"project_ids": "not-a-uuid"}),
        ],
    )
    async def test_bad_parameters(
        self, client: httpx.AsyncClient, tokens: dict[str, str], kind: str, params: dict
    ) -> None:
        response = await client.get(f"/reports/{kind}", params=params)
        assert response.status_code == 400, response.text
        assert response.json()["error"]["code"] == "validation_error"

    async def test_needs_a_token(self, client: httpx.AsyncClient) -> None:
        for kind in ("summary", "detailed", "weekly"):
            assert (await client.get(f"/reports/{kind}", params=WEEK)).status_code == 401
