from __future__ import annotations

import argparse
import logging
import random
import threading
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

import httpx

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")
logger = logging.getLogger("device-simulator")


@dataclass
class DeviceInfo:
    id: int
    name: str
    type: str
    resource_id: Optional[int]


class BackendClient:
    """Minimal client to interact with the backend API."""

    def __init__(self, base_url: str, username: str, password: str, verify_tls: bool) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_tls = verify_tls
        self.token: Optional[str] = None
        self.http = httpx.Client(timeout=10.0, verify=verify_tls)

    def _auth_headers(self) -> Dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def login(self) -> None:
        logger.info("Authenticating as %s", self.username)
        response = self.http.post(
            f"{self.base_url}/login",
            json={"username": self.username, "password": self.password},
        )
        response.raise_for_status()
        payload = response.json()
        self.token = payload["token"]
        logger.info("Authentication successful")

    def list_devices(self) -> List[DeviceInfo]:
        response = self.http.get(
            f"{self.base_url}/devices",
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        devices = [
            DeviceInfo(
                id=item["id"],
                name=item["name"],
                type=item["type"],
                resource_id=item.get("resource_id"),
            )
            for item in response.json()
        ]
        logger.info("Discovered %s devices", len(devices))
        return devices

    def get_resource_status(self, resource_id: int) -> Optional[str]:
        response = self.http.get(
            f"{self.base_url}/resources/{resource_id}",
            headers=self._auth_headers(),
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return data.get("status")

    def report_device_status(
        self,
        device_id: int,
        status: str,
        numeric_value: Optional[float] = None,
        text_value: Optional[str] = None,
    ) -> None:
        payload: Dict[str, Any] = {
            "device_id": device_id,
            "status": status,
            "numeric_value": numeric_value,
            "text_value": text_value,
        }
        response = self.http.post(
            f"{self.base_url}/devices/report",
            json=payload,
        )
        response.raise_for_status()

    def fetch_next_command(self, device_id: int) -> Optional[Dict[str, Any]]:
        response = self.http.post(
            f"{self.base_url}/devices/{device_id}/commands/next",
            headers=self._auth_headers(),
        )
        if response.status_code == 204:
            return None
        response.raise_for_status()
        return response.json()


class DeviceWorker(threading.Thread):
    """Thread responsible for simulating a single device."""

    def __init__(
        self,
        client: BackendClient,
        device: DeviceInfo,
        interval: int,
        stop_event: threading.Event,
    ) -> None:
        super().__init__(daemon=True)
        self.client = client
        self.device = device
        self.interval = interval
        self.stop_event = stop_event

    def run(self) -> None:  # pragma: no cover - threading logic
        logger.info("Starting worker for %s (%s)", self.device.name, self.device.type)
        while not self.stop_event.is_set():
            try:
                self._process_commands()
                self._publish_status()
            except httpx.HTTPError as exc:
                logger.warning("Failed to publish status for %s: %s", self.device.name, exc)
            self.stop_event.wait(self.interval)

    def _publish_status(self) -> None:
        if self.device.type == "sensor":
            temperature = round(random.uniform(20.0, 28.0), 1)
            self.client.report_device_status(
                self.device.id,
                status="active",
                numeric_value=temperature,
                text_value=f"{temperature} C",
            )
        elif self.device.type == "lock":
            status = "locked"
            if self.device.resource_id is not None:
                resource_status = self.client.get_resource_status(self.device.resource_id)
                if resource_status == "reserved":
                    status = "unlocked"
            self.client.report_device_status(self.device.id, status=status)
        else:
            self.client.report_device_status(self.device.id, status="active")

    def _process_commands(self) -> None:
        while not self.stop_event.is_set():
            command = None
            try:
                command = self.client.fetch_next_command(self.device.id)
            except httpx.HTTPError as exc:
                logger.warning("Failed to fetch command for %s: %s", self.device.name, exc)
                return
            if not command:
                return
            self._handle_command(command)

    def _handle_command(self, command: Dict[str, Any]) -> None:
        action = command.get("action")
        payload = command.get("payload") or {}
        logger.info("Executing command %s on %s", action, self.device.name)
        if self.device.type == "lock":
            if action == "unlock":
                self.client.report_device_status(self.device.id, status="unlocked")
            elif action == "lock":
                self.client.report_device_status(self.device.id, status="locked")
            else:
                logger.warning("Unsupported action %s for lock device", action)
                return
        elif self.device.type == "sensor":
            if action == "read":
                self._publish_status()
                return
            logger.warning("Unsupported action %s for sensor device", action)
            return
        else:
            logger.debug("No specific command handling for type %s", self.device.type)
            self.client.report_device_status(self.device.id, status="active")
        if payload.get("reservation_id"):
            logger.debug("Command payload reservation_id=%s", payload["reservation_id"])


class Simulator:
    """Coordinator that spawns device workers."""

    def __init__(self, client: BackendClient, interval: int) -> None:
        self.client = client
        self.interval = interval
        self.stop_event = threading.Event()
        self.workers: List[DeviceWorker] = []

    def start(self) -> None:
        self.client.login()
        devices = self.client.list_devices()
        for device in devices:
            worker = DeviceWorker(self.client, device, self.interval, self.stop_event)
            worker.start()
            self.workers.append(worker)

        logger.info("Simulator running with %s workers", len(self.workers))
        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:  # pragma: no cover
            logger.info("Stopping simulator")
            self.stop()

    def stop(self) -> None:
        self.stop_event.set()
        for worker in self.workers:
            worker.join(timeout=5)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IoT device simulator")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend API base URL")
    parser.add_argument("--username", default="admin", help="Backend username for authentication")
    parser.add_argument("--password", default="admin123", help="Backend password")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Interval in seconds between status updates",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS verification (useful for self-signed certs)",
    )
    return parser.parse_args()


def main() -> None:  # pragma: no cover - CLI wrapper
    args = parse_args()
    client = BackendClient(
        base_url=args.base_url,
        username=args.username,
        password=args.password,
        verify_tls=not args.insecure,
    )
    simulator = Simulator(client, interval=max(args.interval, 5))
    simulator.start()


if __name__ == "__main__":
    main()
