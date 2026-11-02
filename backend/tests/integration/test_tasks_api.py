import httpx
import pytest
import sqlalchemy as sa
from fastapi import FastAPI

from tests.integration.test_api_flow import join, other_user_headers


async def create_project(client: httpx.AsyncClient, name: str = "Website") -> dict:
    response = await client.post("/projects", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


async def create_task(
    client: httpx.AsyncClient, project_id: str, name: str = "Design", **fields: object
) -> httpx.Response:
    return await client.post(
        "/tasks", json={"project_id": project_id, "name": name, **fields}
    )


@pytest.fixture
async def tokens(client: httpx.AsyncClient) -> dict[str, str]:
    from tests.integration.test_api_flow import register_and_login

    return await register_and_login(client)


class TestTaskEndpoints:
    async def test_crud_filters_and_completion(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        project = await create_project(client)
        other_project = await create_project(client, "Other")
        created = await create_task(client, project["id"], estimated_seconds=3600)
        assert created.status_code == 201, created.text
        task = created.json()
        assert task["name"] == "Design"
        assert task["estimated_seconds"] == 3600
        assert task["completed"] is False
        assert task["completed_at"] is None
        assert task["created_at"] == task["updated_at"]

        other = await create_task(client, other_project["id"], "Other task")
        assert other.status_code == 201
        completed = await client.patch(f"/tasks/{task['id']}", json={"completed": True})
        assert completed.status_code == 200
        assert completed.json()["completed"] is True
        assert completed.json()["completed_at"] is not None

        assert (await client.get("/tasks")).json() == [other.json()]
        filtered = await client.get("/tasks", params={"project_id": project["id"]})
        assert filtered.json() == []
        everything = await client.get("/tasks", params={"include_completed": True})
        assert {item["id"] for item in everything.json()} == {task["id"], other.json()["id"]}

        renamed = await client.patch(
            f"/tasks/{task['id']}", json={"name": "Research", "estimated_seconds": None}
        )
        assert renamed.status_code == 200
        assert renamed.json()["name"] == "Research"
        assert renamed.json()["estimated_seconds"] is None
        reopened = await client.patch(f"/tasks/{task['id']}", json={"completed": False})
        assert reopened.json()["completed_at"] is None

        assert (await client.delete(f"/tasks/{task['id']}")).status_code == 204
        remaining = await client.get("/tasks", params={"include_completed": True})
        assert [item["id"] for item in remaining.json()] == [other.json()["id"]]

    async def test_case_insensitive_active_name_conflict_and_reopen(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        project = await create_project(client)
        first = (await create_task(client, project["id"])).json()
        duplicate = await create_task(client, project["id"], "DESIGN")
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "task_name_taken"

        await client.patch(f"/tasks/{first['id']}", json={"completed": True})
        second = (await create_task(client, project["id"], "design")).json()
        conflict = await client.patch(f"/tasks/{first['id']}", json={"completed": False})
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "task_name_taken"
        await client.delete(f"/tasks/{second['id']}")
        assert (
            await client.patch(f"/tasks/{first['id']}", json={"completed": False})
        ).status_code == 200

    @pytest.mark.parametrize("estimated_seconds", [0, -1])
    async def test_estimate_must_be_positive(
        self, client: httpx.AsyncClient, tokens: dict[str, str], estimated_seconds: int
    ) -> None:
        project = await create_project(client)
        response = await create_task(
            client, project["id"], estimated_seconds=estimated_seconds
        )
        assert response.status_code == 400

    async def test_archived_project_is_read_only(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        project = await create_project(client)
        task = (await create_task(client, project["id"])).json()
        await client.patch(f"/projects/{project['id']}", json={"archived": True})

        assert (await client.get("/tasks")).json()[0]["id"] == task["id"]
        for method, path, body in (
            ("POST", "/tasks", {"project_id": project["id"], "name": "New"}),
            ("PATCH", f"/tasks/{task['id']}", {"name": "New"}),
            ("PATCH", f"/tasks/{task['id']}", {"completed": True}),
            ("DELETE", f"/tasks/{task['id']}", None),
        ):
            response = await client.request(method, path, json=body)
            assert response.status_code == 400, response.text

    async def test_workspace_and_project_isolation(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        project = await create_project(client)
        task = (await create_task(client, project["id"])).json()
        other = await other_user_headers(client)

        assert (await client.get("/tasks", headers=other)).json() == []
        assert (
            await client.get("/tasks", params={"project_id": project["id"]}, headers=other)
        ).status_code == 404
        borrowed = await client.post(
            "/tasks", json={"project_id": project["id"], "name": "Stolen"}, headers=other
        )
        assert borrowed.status_code == 404
        patched = await client.patch(
            f"/tasks/{task['id']}", json={"name": "Stolen"}, headers=other
        )
        assert patched.status_code == 404
        assert (await client.delete(f"/tasks/{task['id']}", headers=other)).status_code == 404

    async def test_member_can_list_and_create_but_not_mutate(
        self, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        workspace = (await client.get("/auth/me")).json()["default_workspace_id"]
        project = await create_project(client)
        task = (await create_task(client, project["id"])).json()
        member = await other_user_headers(client)
        await join(client, workspace, member)
        prefix = f"/workspaces/{workspace}"

        listed = await client.get(f"{prefix}/tasks", headers=member)
        assert [item["id"] for item in listed.json()] == [task["id"]]
        created = await client.post(
            f"{prefix}/tasks",
            json={"project_id": project["id"], "name": "Member task"},
            headers=member,
        )
        assert created.status_code == 201, created.text
        for method, path, body in (
            ("PATCH", f"/tasks/{task['id']}", {"name": "Stolen"}),
            ("PATCH", f"/tasks/{task['id']}", {"completed": True}),
            ("DELETE", f"/tasks/{task['id']}", None),
        ):
            response = await client.request(method, prefix + path, json=body, headers=member)
            assert response.status_code == 403, response.text

    async def test_project_delete_cascades_tasks(
        self, app: FastAPI, client: httpx.AsyncClient, tokens: dict[str, str]
    ) -> None:
        project = await create_project(client)
        task = (await create_task(client, project["id"])).json()
        await client.delete(f"/projects/{project['id']}")
        async with app.state.sessionmaker() as session:
            count = await session.execute(
                sa.text("SELECT count(*) FROM tasks WHERE id = :task_id"), {"task_id": task["id"]}
            )
            assert count.scalar_one() == 0
