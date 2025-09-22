import os
import sys
import pytest

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Provide a test client with proper resource cleanup."""
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "IoT Management System API" in response.json()["message"]


def test_login_success(client):
    """Test successful login."""
    response = client.post("/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["role"] == "admin"
    assert data["username"] == "admin"


def test_login_failure(client):
    """Test failed login with invalid credentials."""
    response = client.post("/login", json={
        "username": "invalid",
        "password": "invalid"
    })
    assert response.status_code == 401


def test_devices_without_auth(client):
    """Test devices endpoint without authentication."""
    response = client.get("/devices")
    assert response.status_code == 401


def test_devices_with_auth(client):
    """Test devices endpoint with authentication."""
    login_response = client.post("/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["token"]

    response = client.get(
        "/devices",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    devices = response.json()
    assert isinstance(devices, list)
    assert len(devices) >= 0


def test_resources_with_auth(client):
    """Test resources endpoint with authentication."""
    login_response = client.post("/login", json={
        "username": "user",
        "password": "user123"
    })
    token = login_response.json()["token"]

    response = client.get(
        "/resources",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    resources = response.json()
    assert isinstance(resources, list)


def test_device_action_with_auth(client):
    """Test device action with authentication."""
    login_response = client.post("/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["token"]

    response = client.post(
        "/devices/1/action",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "unlock"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True


def test_reserve_resource(client):
    """Test resource reservation."""
    login_response = client.post("/login", json={
        "username": "user",
        "password": "user123"
    })
    token = login_response.json()["token"]

    response = client.post(
        "/resources/1/reserve",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": 2}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__])
