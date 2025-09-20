import pytest
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "IoT Management System API" in response.json()["message"]


def test_login_success():
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


def test_login_failure():
    """Test failed login with invalid credentials."""
    response = client.post("/login", json={
        "username": "invalid",
        "password": "invalid"
    })
    assert response.status_code == 401


def test_devices_without_auth():
    """Test devices endpoint without authentication."""
    response = client.get("/devices")
    assert response.status_code == 401


def test_devices_with_auth():
    """Test devices endpoint with authentication."""
    # First login to get token
    login_response = client.post("/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["token"]
    
    # Then access devices endpoint
    response = client.get("/devices", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    devices = response.json()
    assert isinstance(devices, list)
    assert len(devices) >= 0


def test_resources_with_auth():
    """Test resources endpoint with authentication."""
    # First login to get token
    login_response = client.post("/login", json={
        "username": "user",
        "password": "user123"
    })
    token = login_response.json()["token"]
    
    # Then access resources endpoint
    response = client.get("/resources", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    resources = response.json()
    assert isinstance(resources, list)


def test_device_action_with_auth():
    """Test device action with authentication."""
    # First login to get token
    login_response = client.post("/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["token"]
    
    # Then execute device action
    response = client.post("/devices/1/action", 
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "unlock"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True


def test_reserve_resource():
    """Test resource reservation."""
    # Login as user
    login_response = client.post("/login", json={
        "username": "user",
        "password": "user123"
    })
    token = login_response.json()["token"]
    
    # Reserve resource
    response = client.post("/resources/1/reserve",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": 2}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__])