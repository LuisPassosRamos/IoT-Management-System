import json
import os
import shutil
import sys
import pytest

BASE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.join(BASE_DIR, "..")
SOURCE_DB = os.path.join(ROOT_DIR, "data", "db.json")
TEST_DB = os.path.join(BASE_DIR, "test_db.json")

os.environ["DB_FILE_PATH"] = TEST_DB

if os.path.exists(SOURCE_DB):
    shutil.copyfile(SOURCE_DB, TEST_DB)
else:
    default_payload = {
        "users": [],
        "devices": [],
        "resources": [],
        "reservations": [],
    }
    with open(TEST_DB, "w", encoding="utf-8") as handler:
        json.dump(default_payload, handler)

sys.path.insert(0, ROOT_DIR)

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(autouse=True)
def reset_database() -> None:
    """Reset JSON database before each test run."""
    shutil.copyfile(SOURCE_DB, TEST_DB)
    yield


@pytest.fixture(scope="module")
def client():
    """Provide a test client with proper resource cleanup."""
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str, password: str) -> dict:
    response = client.post(
        "/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "IoT Management System API" in response.json()["message"]


def test_login_success(client):
    data = login(client, "admin", "admin123")
    assert "token" in data
    assert data["role"] == "admin"
    assert data["username"] == "admin"
    assert data["user_id"] == 1


def test_login_failure(client):
    response = client.post(
        "/login", json={"username": "invalid", "password": "invalid"}
    )
    assert response.status_code == 401


def test_devices_without_auth(client):
    response = client.get("/devices")
    assert response.status_code == 401


def test_devices_with_auth(client):
    data = login(client, "admin", "admin123")
    response = client.get(
        "/devices",
        headers=auth_headers(data["token"]),
    )
    assert response.status_code == 200
    devices = response.json()
    assert isinstance(devices, list)


def test_get_single_device(client):
    data = login(client, "admin", "admin123")
    response = client.get(
        "/devices/1",
        headers=auth_headers(data["token"]),
    )
    assert response.status_code == 200
    device = response.json()
    assert device["id"] == 1


def test_resources_with_auth(client):
    data = login(client, "user", "user123")
    response = client.get(
        "/resources",
        headers=auth_headers(data["token"]),
    )
    assert response.status_code == 200
    resources = response.json()
    assert isinstance(resources, list)


def test_admin_manage_resources(client):
    admin = login(client, "admin", "admin123")
    headers = auth_headers(admin["token"])

    create_response = client.post(
        "/resources",
        headers=headers,
        json={
            "name": "Sala 200",
            "description": "Espaco multiuso",
        },
    )
    assert create_response.status_code == 201
    created_resource = create_response.json()
    resource_id = created_resource["id"]
    assert created_resource["available"] is True

    update_response = client.put(
        f"/resources/{resource_id}",
        headers=headers,
        json={"description": "Espaco multiuso atualizado"},
    )
    assert update_response.status_code == 200
    assert (
        update_response.json()["description"]
        == "Espaco multiuso atualizado"
    )

    delete_response = client.delete(
        f"/resources/{resource_id}", headers=headers
    )
    assert delete_response.status_code == 204


def test_admin_manage_devices(client):
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
    created_device = create_response.json()
    device_id = created_device["id"]

    update_response = client.put(
        f"/devices/{device_id}",
        headers=headers,
        json={"status": "inactive"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "inactive"

    delete_response = client.delete(
        f"/devices/{device_id}", headers=headers
    )
    assert delete_response.status_code == 204


def test_reservation_flow(client):
    user = login(client, "user", "user123")
    user_headers = auth_headers(user["token"])

    reserve_response = client.post(
        "/resources/1/reserve",
        headers=user_headers,
        json={"user_id": user["user_id"]},
    )
    assert reserve_response.status_code == 200
    reservation = reserve_response.json()
    assert reservation["status"] == "active"

    release_response = client.post(
        "/resources/1/release",
        headers=user_headers,
    )
    assert release_response.status_code == 200
    resource = release_response.json()
    assert resource["available"] is True
    assert resource["reserved_by"] is None


def test_admin_list_reservations(client):
    user = login(client, "user", "user123")
    user_headers = auth_headers(user["token"])
    client.post(
        "/resources/1/reserve",
        headers=user_headers,
        json={"user_id": user["user_id"]},
    )

    admin = login(client, "admin", "admin123")
    admin_headers = auth_headers(admin["token"])

    response = client.get("/reservations", headers=admin_headers)
    assert response.status_code == 200
    reservations = response.json()
    assert isinstance(reservations, list)
    assert len(reservations) >= 1
    first_reservation = reservations[0]
    assert "resource_name" in first_reservation
    assert "username" in first_reservation


def test_reservations_requires_admin(client):
    user = login(client, "user", "user123")
    response = client.get(
        "/reservations", headers=auth_headers(user["token"])
    )
    assert response.status_code == 403


def test_admin_cancel_reservation(client):
    user = login(client, "user", "user123")
    user_headers = auth_headers(user["token"])
    reserve_response = client.post(
        "/resources/1/reserve",
        headers=user_headers,
        json={"user_id": user["user_id"]},
    )
    reservation_id = reserve_response.json()["id"]

    admin = login(client, "admin", "admin123")
    admin_headers = auth_headers(admin["token"])

    patch_response = client.patch(
        f"/reservations/{reservation_id}",
        headers=admin_headers,
        json={"status": "cancelled"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "cancelled"

    resource_response = client.get(
        "/resources",
        headers=admin_headers,
    )
    resource = next(
        item for item in resource_response.json() if item["id"] == 1
    )
    assert resource["available"] is True


def test_device_action_with_auth(client):
    admin = login(client, "admin", "admin123")
    response = client.post(
        "/devices/1/action",
        headers=auth_headers(admin["token"]),
        json={"action": "unlock"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
