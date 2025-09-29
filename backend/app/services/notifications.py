from __future__ import annotations

import asyncio
from typing import Any, Dict, Set

from fastapi import WebSocket


class WebSocketManager:
    """Keep track of websocket connections and broadcast events."""

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        dead: Set[WebSocket] = set()
        async with self._lock:
            for connection in list(self._connections):
                try:
                    await connection.send_json(message)
                except Exception:
                    dead.add(connection)
            for connection in dead:
                self._connections.discard(connection)

    def schedule_broadcast(self, message: Dict[str, Any]) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(self.broadcast(message))


manager = WebSocketManager()
