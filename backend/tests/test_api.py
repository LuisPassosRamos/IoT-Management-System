import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(__file__).parent / "test_iot.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"  # noqa: E501

from app.db.base import Base
from app.db.session import engine
from app.db.init_db import init_db
from app.main import app


@pytest.fixture(autouse=True)
def reset_database() -> None:
    """Reset the SQLite database before each test run."""

    Base.metadata.drop_all(bind=engine)
    init_db()
    yield


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Provide a test client for API calls."""

    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str, password: str) -> dict:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_success(client: TestClient) -> None:
    data = login(client, "admin", "admin123")
    assert data["role"] == "admin"
    assert "token" in data


def test_login_failure(client: TestClient) -> None:
    response = client.post("/login", json={"username": "ghost", "password": "nope"})
    assert response.status_code == 401


def test_user_can_list_permitted_resources(client: TestClient) -> None:
    user = login(client, "user", "user123")
    response = client.get("/resources", headers=auth_headers(user["token"]))
    assert response.status_code == 200
    resources = response.json()
    assert len(resources) >= 1
    assert all("status" in item for item in resources)


def test_admin_crud_resource(client: TestClient) -> None:
    admin = login(client, "admin", "admin123")
    headers = auth_headers(admin["token"])

    create_payload = {
        "name": "Sala Maker",
        "description": "Espaco colaborativo",
        "type": "lab",
        "location": "Bloco C",
        "capacity": 8,
    }
    create_response = client.post("/resources", headers=headers, json=create_payload)
    assert create_response.status_code == 201
    resource_id = create_response.json()["id"]

    update_response = client.put(
        f"/resources/{resource_id}",
        headers=headers,
        json={"status": "maintenance", "capacity": 12},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "maintenance"
    assert update_response.json()["capacity"] == 12

    delete_response = client.delete(f"/resources/{resource_id}", headers=headers)
    assert delete_response.status_code == 204


def test_admin_manage_device(client: TestClient) -> None:
    admin = login(client, "admin", "admin123")
    headers = auth_headers(admin["token"])

    create_response = client.post(
        "/devices",
        headers=headers,
        json={
            "name": "Sensor Luminosidade",
            "type": "sensor",
            "status": "active",
        },
    )
    assert create_response.status_code == 201
    device_id = create_response.json()["id"]

    get_response = client.get(f"/devices/{device_id}", headers=headers)
    assert get_response.status_code == 200

    update_response = client.put(
        f"/devices/{device_id}",
        headers=headers,
        json={"status": "inactive"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "inactive"

    delete_response = client.delete(f"/devices/{device_id}", headers=headers)
    assert delete_response.status_code == 204


def test_reservation_create_and_release(client: TestClient) -> None:
    user = login(client, "user", "user123")
    headers = auth_headers(user["token"])

    reserve_response = client.post(
        "/resources/1/reserve",
        headers=headers,
        json={"duration_minutes": 30},
    )
    assert reserve_response.status_code == 200
    reservation_id = reserve_response.json()["id"]
    assert reserve_response.json()["status"] == "active"

    release_response = client.post(
        "/resources/1/release",
        headers=headers,
        json={"notes": "Uso concluido"},
    )
    assert release_response.status_code == 200
    assert release_response.json()["status"] in {"completed", "cancelled"}
    assert release_response.json()["id"] == reservation_id


def test_reservation_conflict(client: TestClient) -> None:
    user = login(client, "user", "user123")
    headers = auth_headers(user["token"])
    client.post(
        "/resources/1/reserve",
        headers=headers,
        json={"duration_minutes": 30},
    )

    conflict_response = client.post(
        "/resources/1/reserve",
        headers=headers,
        json={"duration_minutes": 60},
    )
    assert conflict_response.status_code == 409




def test_device_command_flow(client: TestClient) -> None:
    admin = login(client, "admin", "admin123")
    headers = auth_headers(admin["token"])

    reserve_response = client.post(
        
        "/resources/1/reserve",
        headers=headers,
        json={"duration_minutes": 30},
    )
    assert reserve_response.status_code == 200

    command_response = client.post(
        "/devices/1/commands/next", headers=headers
    )
    assert command_response.status_code == 200
    command_json = command_response.json()
    assert command_json["action"] == "unlock"

    next_response = client.post("/devices/1/commands/next", headers=headers)
    assert next_response.status_code == 204

    release_response = client.post(
        "/resources/1/release",
        headers=headers,
        json={"force": True},
    )
    assert release_response.status_code == 200

    lock_command = client.post("/devices/1/commands/next", headers=headers)
    assert lock_command.status_code == 200
    assert lock_command.json()["action"] == "lock"

def test_admin_export_reservations_csv(client: TestClient) -> None:
    admin = login(client, "admin", "admin123")
    headers = auth_headers(admin["token"])

    response = client.get("/reservations/export?format=csv", headers=headers)
    assert response.status_code == 200, response.json()
    assert "text/csv" in response.headers.get("content-type", "")


def test_audit_logs_admin_access(client: TestClient) -> None:
    admin = login(client, "admin", "admin123")
    headers = auth_headers(admin["token"])
    response = client.get("/audit-logs", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_audit_logs_user_denied(client: TestClient) -> None:
    user = login(client, "user", "user123")
    response = client.get("/audit-logs", headers=auth_headers(user["token"]))
    assert response.status_code == 403
