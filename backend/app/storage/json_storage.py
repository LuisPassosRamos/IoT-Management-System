import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_FILE = os.path.join(DATA_DIR, "db.json")


class JSONStorage:
    """Simple JSON file storage for prototyping."""
    
    def __init__(self):
        self._ensure_data_dir()
    
    def _ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def load_data(self) -> Dict[str, Any]:
        """Load data from JSON file."""
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_data()
        except json.JSONDecodeError:
            return self._get_default_data()
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """Save data to JSON file."""
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _get_default_data(self) -> Dict[str, Any]:
        """Return default data structure."""
        return {
            "users": [],
            "devices": [],
            "resources": [],
            "reservations": []
        }
    
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
    
    def update_device(self, device_id: int, updates: Dict[str, Any]) -> bool:
        """Update device data."""
        data = self.load_data()
        devices = data.get("devices", [])
        
        for device in devices:
            if device["id"] == device_id:
                device.update(updates)
                self.save_data(data)
                return True
        return False
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Get all resources."""
        data = self.load_data()
        return data.get("resources", [])
    
    def get_resource_by_id(self, resource_id: int) -> Optional[Dict[str, Any]]:
        """Get resource by ID."""
        resources = self.get_resources()
        return next((r for r in resources if r["id"] == resource_id), None)
    
    def update_resource(self, resource_id: int, updates: Dict[str, Any]) -> bool:
        """Update resource data."""
        data = self.load_data()
        resources = data.get("resources", [])
        
        for resource in resources:
            if resource["id"] == resource_id:
                resource.update(updates)
                self.save_data(data)
                return True
        return False
    
    def get_reservations(self) -> List[Dict[str, Any]]:
        """Get all reservations."""
        data = self.load_data()
        return data.get("reservations", [])
    
    def add_reservation(self, reservation: Dict[str, Any]) -> None:
        """Add new reservation."""
        data = self.load_data()
        reservations = data.get("reservations", [])
        
        # Generate new ID
        new_id = max([r.get("id", 0) for r in reservations], default=0) + 1
        reservation["id"] = new_id
        reservation["timestamp"] = datetime.now().isoformat()
        
        reservations.append(reservation)
        self.save_data(data)
    
    def get_user_by_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Get user by username and password."""
        users = self.get_users()
        return next((u for u in users if u["username"] == username and u["password"] == password), None)


# Global storage instance
storage = JSONStorage()