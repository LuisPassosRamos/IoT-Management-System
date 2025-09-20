from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import random


class IoTDevice(ABC):
    """Abstract base class for IoT devices."""
    
    def __init__(self, device_id: int, name: str):
        self.device_id = device_id
        self.name = name
    
    @abstractmethod
    def execute_action(self, action: str) -> Dict[str, Any]:
        """Execute an action on the device."""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get current device status."""
        pass


class Lock(IoTDevice):
    """Simulated IoT lock device."""
    
    def __init__(self, device_id: int, name: str, initial_status: str = "locked"):
        super().__init__(device_id, name)
        self.status = initial_status
    
    def execute_action(self, action: str) -> Dict[str, Any]:
        """Execute lock action (lock/unlock)."""
        if action == "unlock":
            self.status = "unlocked"
            return {
                "success": True,
                "message": f"Device {self.name} unlocked successfully",
                "status": self.status
            }
        elif action == "lock":
            self.status = "locked"
            return {
                "success": True,
                "message": f"Device {self.name} locked successfully",
                "status": self.status
            }
        else:
            return {
                "success": False,
                "message": f"Invalid action '{action}' for lock device",
                "status": self.status
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current lock status."""
        return {
            "id": self.device_id,
            "name": self.name,
            "type": "lock",
            "status": self.status
        }


class Sensor(IoTDevice):
    """Simulated IoT sensor device."""
    
    def __init__(self, device_id: int, name: str, initial_status: str = "active"):
        super().__init__(device_id, name)
        self.status = initial_status
        self.value = 24.5  # Default temperature value
    
    def execute_action(self, action: str) -> Dict[str, Any]:
        """Execute sensor action (read/activate/deactivate)."""
        if action == "read":
            # Simulate sensor reading with some variation
            self.value = round(random.uniform(20.0, 30.0), 1)
            return {
                "success": True,
                "message": f"Sensor {self.name} reading updated",
                "status": self.status,
                "value": self.value
            }
        elif action == "activate":
            self.status = "active"
            return {
                "success": True,
                "message": f"Sensor {self.name} activated",
                "status": self.status,
                "value": self.value
            }
        elif action == "deactivate":
            self.status = "inactive"
            return {
                "success": True,
                "message": f"Sensor {self.name} deactivated",
                "status": self.status,
                "value": self.value
            }
        else:
            return {
                "success": False,
                "message": f"Invalid action '{action}' for sensor device",
                "status": self.status,
                "value": self.value
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current sensor status."""
        return {
            "id": self.device_id,
            "name": self.name,
            "type": "sensor",
            "status": self.status,
            "value": self.value
        }


class DeviceSimulator:
    """Manages IoT device simulations."""
    
    def __init__(self):
        self.devices: Dict[int, IoTDevice] = {}
    
    def register_device(self, device_data: Dict[str, Any]) -> None:
        """Register a device from JSON data."""
        device_id = device_data["id"]
        name = device_data["name"]
        device_type = device_data["type"]
        status = device_data["status"]
        
        if device_type == "lock":
            self.devices[device_id] = Lock(device_id, name, status)
        elif device_type == "sensor":
            sensor = Sensor(device_id, name, status)
            if "value" in device_data:
                sensor.value = device_data["value"]
            self.devices[device_id] = sensor
    
    def get_device(self, device_id: int) -> Optional[IoTDevice]:
        """Get device by ID."""
        return self.devices.get(device_id)
    
    def execute_device_action(self, device_id: int, action: str) -> Dict[str, Any]:
        """Execute action on device."""
        device = self.get_device(device_id)
        if not device:
            return {
                "success": False,
                "message": f"Device with ID {device_id} not found"
            }
        
        return device.execute_action(action)
    
    def get_device_status(self, device_id: int) -> Optional[Dict[str, Any]]:
        """Get device status."""
        device = self.get_device(device_id)
        return device.get_status() if device else None
    
    def get_all_devices_status(self) -> Dict[int, Dict[str, Any]]:
        """Get status of all devices."""
        return {
            device_id: device.get_status() 
            for device_id, device in self.devices.items()
        }


# Global device simulator instance
device_simulator = DeviceSimulator()