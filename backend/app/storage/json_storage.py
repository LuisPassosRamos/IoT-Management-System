import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

DB_FILE_ENV = os.getenv("DB_FILE_PATH")
if DB_FILE_ENV:
    DB_FILE = DB_FILE_ENV
    DATA_DIR = os.path.dirname(DB_FILE_ENV) or "."
else:
    if os.path.exists("data/db.json"):
        DATA_DIR = "data"
    else:
        DATA_DIR = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "data"
        )
    DB_FILE = os.path.join(DATA_DIR, "db.json")


class JSONStorage:
    """Simple JSON file storage for prototyping."""

    def __init__(self) -> None:
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        target_dir = os.path.dirname(DB_FILE) or "."
        os.makedirs(target_dir, exist_ok=True)

    def load_data(self) -> Dict[str, Any]:
        """Load data from JSON file."""
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_data()
        except json.JSONDecodeError:
            return self._get_default_data()

    def save_data(self, data: Dict[str, Any]) -> None:
        """Save data to JSON file."""
        self._ensure_data_dir()
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_default_data(self) -> Dict[str, Any]:
        """Return default data structure."""
        return {
            "users": [],
            "devices": [],
            "resources": [],
            "reservations": [],
        }

    def _generate_id(self, items: List[Dict[str, Any]]) -> int:
        """Generate next incremental ID for a collection."""
        return max((item.get("id", 0) for item in items), default=0) + 1

    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        data = self.load_data()
        return data.get("users", [])

    def get_devices(self) -> List[Dict[str, Any]]:
        """Get all devices."""
        data = self.load_data()
        return data.get("devices", [])

    def get_device_by_id(self, device_id: int) -> Optional[Dict[str, Any]]:
        """Get device by ID."""
        devices = self.get_devices()
        return next((d for d in devices if d["id"] == device_id), None)

    def add_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new device entry."""
        data = self.load_data()
        devices = data.setdefault("devices", [])
        new_device = {"id": self._generate_id(devices), **device_data}
        devices.append(new_device)
        self.save_data(data)
        return new_device

    def update_device(self, device_id: int, updates: Dict[str, Any]) -> bool:
        """Update device data."""
        data = self.load_data()
        devices = data.get("devices", [])

        allow_none = {"resource_id", "value"}
        updated = False
        for device in devices:
            if device["id"] == device_id:
                for key, value in updates.items():
                    if value is None and key not in allow_none:
                        continue
                    device[key] = value
                updated = True
                break

        if updated:
            self.save_data(data)
        return updated

    def delete_device(self, device_id: int) -> bool:
        """Delete device and detach from any linked resource."""
        data = self.load_data()
        devices = data.get("devices", [])
        new_devices = [device for device in devices if device["id"] != device_id]
        if len(new_devices) == len(devices):
            return False

        data["devices"] = new_devices

        for resource in data.get("resources", []):
            if resource.get("device_id") == device_id:
                resource["device_id"] = None

        self.save_data(data)
        return True

    def get_resources(self) -> List[Dict[str, Any]]:
        """Get all resources."""
        data = self.load_data()
        return data.get("resources", [])

    def get_resource_by_id(self, resource_id: int) -> Optional[Dict[str, Any]]:
        """Get resource by ID."""
        resources = self.get_resources()
        return next((r for r in resources if r["id"] == resource_id), None)

    def add_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource entry."""
        data = self.load_data()
        resources = data.setdefault("resources", [])
        default_data = {
            "available": True,
            "reserved_by": None,
        }
        new_resource = {
            "id": self._generate_id(resources),
            **default_data,
            **resource_data,
        }
        resources.append(new_resource)
        self.save_data(data)
        return new_resource

    def update_resource(
        self, resource_id: int, updates: Dict[str, Any]
    ) -> bool:
        """Update resource data."""
        data = self.load_data()
        resources = data.get("resources", [])

        allow_none = {"reserved_by", "device_id"}
        updated = False
        for resource in resources:
            if resource["id"] == resource_id:
                for key, value in updates.items():
                    if value is None and key not in allow_none:
                        continue
                    resource[key] = value
                updated = True
                break

        if updated:
            self.save_data(data)
        return updated

    def delete_resource(self, resource_id: int) -> bool:
        """Delete resource and clean related references."""
        data = self.load_data()
        resources = data.get("resources", [])
        new_resources = [r for r in resources if r["id"] != resource_id]
        if len(new_resources) == len(resources):
            return False

        data["resources"] = new_resources

        for device in data.get("devices", []):
            if device.get("resource_id") == resource_id:
                device["resource_id"] = None

        for reservation in data.get("reservations", []):
            if reservation.get("resource_id") == resource_id and reservation.get("status") == "active":
                reservation["status"] = "cancelled"

        self.save_data(data)
        return True

    def get_reservations(self) -> List[Dict[str, Any]]:
        """Get all reservations."""
        data = self.load_data()
        return data.get("reservations", [])

    def get_reservation_by_id(self, reservation_id: int) -> Optional[Dict[str, Any]]:
        """Get reservation by ID."""
        reservations = self.get_reservations()
        return next((r for r in reservations if r["id"] == reservation_id), None)

    def add_reservation(self, reservation: Dict[str, Any]) -> Dict[str, Any]:
        """Add new reservation."""
        data = self.load_data()
        reservations = data.setdefault("reservations", [])

        new_reservation = reservation.copy()
        new_reservation["id"] = self._generate_id(reservations)
        new_reservation["timestamp"] = datetime.now().isoformat()
        reservations.append(new_reservation)
        self.save_data(data)
        return new_reservation

    def update_reservation(
        self, reservation_id: int, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update reservation details."""
        data = self.load_data()
        reservations = data.get("reservations", [])

        for reservation in reservations:
            if reservation["id"] == reservation_id:
                for key, value in updates.items():
                    if value is None:
                        continue
                    reservation[key] = value
                self.save_data(data)
                return reservation
        return None

    def delete_reservation(self, reservation_id: int) -> bool:
        """Delete reservation by ID."""
        data = self.load_data()
        reservations = data.get("reservations", [])
        new_reservations = [r for r in reservations if r["id"] != reservation_id]
        if len(new_reservations) == len(reservations):
            return False
        data["reservations"] = new_reservations
        self.save_data(data)
        return True

    def get_user_by_credentials(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Get user by username and password."""
        users = self.get_users()
        return next(
            (
                u
                for u in users
                if u["username"] == username and u["password"] == password
            ),
            None,
        )


storage = JSONStorage()
