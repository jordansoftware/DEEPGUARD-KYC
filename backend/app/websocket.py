"""Real-time WebSocket updates for KYC case changes.

Tenant isolation: a socket only ever receives updates for cases owned by the
client that authenticated it. Subscriptions are checked against the database,
and notifications are delivered only to sockets of the target client.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from .db import get_db_sync
from .models import Case, Client
from .security import hash_api_key

logger = logging.getLogger("deepguard.websocket")

router = APIRouter(tags=["websocket"])

# case_id -> sockets subscribed to that case (only after an ownership check)
connected_clients: dict[int, list[WebSocket]] = {}
# every open authenticated socket -> owning client id
socket_owners: dict[WebSocket, int] = {}


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


def _client_owns_case(client_id: int, case_id: int) -> bool:
    db = get_db_sync()
    try:
        return db.scalar(
            select(Case.id).where(Case.id == case_id, Case.client_id == client_id)
        ) is not None
    finally:
        db.close()


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
    client_id = client.id
    socket_owners[websocket] = client_id
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                continue
            if not isinstance(msg, dict):
                continue
            if msg.get("type") == "subscribe":
                try:
                    case_id = int(msg.get("case_id"))
                except (TypeError, ValueError):
                    continue
                if not _client_owns_case(client_id, case_id):
                    logger.warning("Client %s attempted to subscribe to foreign case %s", client_id, case_id)
                    continue
                subs = connected_clients.setdefault(case_id, [])
                if websocket not in subs:
                    subs.append(websocket)
            elif msg.get("type") == "unsubscribe":
                try:
                    case_id = int(msg.get("case_id"))
                except (TypeError, ValueError):
                    continue
                if case_id in connected_clients:
                    connected_clients[case_id] = [
                        ws for ws in connected_clients[case_id] if ws is not websocket
                    ]
    except WebSocketDisconnect:
        _cleanup(websocket)
    except Exception:
        logger.exception("WebSocket error")
        _cleanup(websocket)


def _cleanup(websocket: WebSocket):
    socket_owners.pop(websocket, None)
    for case_id in list(connected_clients.keys()):
        connected_clients[case_id] = [
            ws for ws in connected_clients[case_id] if ws is not websocket
        ]


async def _send(sockets: list[WebSocket], message: str) -> None:
    disconnected = []
    for ws in sockets:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        _cleanup(ws)


async def broadcast_case_update(case_id: int, data: dict[str, Any]):
    """Send a case update only to sockets subscribed to that case (already owner-checked)."""
    message = json.dumps({"type": "case_update", "case_id": case_id, "data": data})
    await _send(list(connected_clients.get(case_id, [])), message)


async def broadcast_notification(client_id: int, data: dict[str, Any]):
    """Send a notification only to the sockets authenticated as `client_id`."""
    message = json.dumps({"type": "notification", "data": data})
    targets = [ws for ws, owner in socket_owners.items() if owner == client_id]
    await _send(targets, message)


def get_connected_count() -> int:
    """Get the number of connected WebSocket clients."""
    return len(socket_owners)
