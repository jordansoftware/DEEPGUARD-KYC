"""Real-time WebSocket updates for KYC case changes."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from .db import get_db_sync
from .models import Client
from .security import hash_api_key

logger = logging.getLogger("deepguard.websocket")

router = APIRouter(tags=["websocket"])

connected_clients: dict[int, list[WebSocket]] = {}
all_clients: list[WebSocket] = []


async def _authenticate_ws(websocket: WebSocket) -> Client | None:
    """Authenticate WebSocket connection via API key in query params."""
    api_key = websocket.query_params.get("api_key")
    if not api_key:
        return None
    db = get_db_sync()
    try:
        hashed = hash_api_key(api_key)
        client = db.scalar(select(Client).where(Client.api_key == hashed))
        if client and client.active:
            return client
    finally:
        db.close()
    return None


@router.websocket("/ws/cases")
async def ws_cases(websocket: WebSocket):
    """WebSocket endpoint for real-time case updates.

    Connect with: ws://localhost:8765/ws/cases?api_key=dg_your_key
    """
    client = await _authenticate_ws(websocket)
    if not client:
        await websocket.close(code=4001, reason="Invalid or missing API key")
        return

    await websocket.accept()
    all_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                continue
            if msg.get("type") == "subscribe":
                case_id = msg.get("case_id")
                if case_id:
                    connected_clients.setdefault(case_id, []).append(websocket)
            elif msg.get("type") == "unsubscribe":
                case_id = msg.get("case_id")
                if case_id and case_id in connected_clients:
                    connected_clients[case_id] = [
                        ws for ws in connected_clients[case_id] if ws != websocket
                    ]
    except WebSocketDisconnect:
        _cleanup(websocket)
    except Exception:
        logger.exception("WebSocket error")
        _cleanup(websocket)


def _cleanup(websocket: WebSocket):
    if websocket in all_clients:
        all_clients.remove(websocket)
    for case_id in list(connected_clients.keys()):
        connected_clients[case_id] = [
            ws for ws in connected_clients[case_id] if ws != websocket
        ]


async def broadcast_case_update(case_id: int, data: dict[str, Any]):
    """Broadcast a case update to all subscribed clients."""
    message = json.dumps({"type": "case_update", "case_id": case_id, "data": data})
    clients = connected_clients.get(case_id, []) + all_clients
    disconnected = []
    for ws in clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        _cleanup(ws)


async def broadcast_notification(data: dict[str, Any]):
    """Broadcast a general notification to all connected clients."""
    message = json.dumps({"type": "notification", "data": data})
    disconnected = []
    for ws in all_clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        _cleanup(ws)


def get_connected_count() -> int:
    """Get the number of connected WebSocket clients."""
    return len(all_clients)
