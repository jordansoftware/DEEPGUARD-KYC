"""Plugin system — extensible integrations for DeepGuard."""

from __future__ import annotations

import ipaddress
import json
import logging
import urllib.request
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Client, PluginConfig
from app.security import current_client

logger = logging.getLogger("deepguard.plugins")

router = APIRouter(prefix="/api/plugins", tags=["plugins"])
settings = get_settings()

BUILTIN_PLUGINS = {
    "slack": {
        "name": "Slack",
        "description": "Send case notifications to Slack channels.",
        "config_fields": ["webhook_url", "channel"],
        "allowed_domains": ["hooks.slack.com"],
    },
    "telegram": {
        "name": "Telegram",
        "description": "Send case notifications to Telegram chats.",
        "config_fields": ["bot_token", "chat_id"],
        "allowed_domains": ["api.telegram.org"],
    },
    "discord": {
        "name": "Discord",
        "description": "Send case notifications to Discord webhooks.",
        "config_fields": ["webhook_url"],
        "allowed_domains": ["discord.com", "discordapp.com"],
    },
    "zapier": {
        "name": "Zapier",
        "description": "Trigger Zapier webhooks on case events.",
        "config_fields": ["webhook_url"],
        "allowed_domains": ["hooks.zapier.com"],
    },
    "email": {
        "name": "Email",
        "description": "Send email notifications on case events.",
        "config_fields": ["recipient", "events"],
        "allowed_domains": [],
    },
}

SENSITIVE_KEYS = {"bot_token", "webhook_url", "secret", "password", "token"}


def _is_safe_url(url: str, allowed_domains: list[str] | None = None) -> bool:
    """Block requests to private/internal addresses (SSRF protection)."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return False
    # Check against allowed domains for known services
    if allowed_domains:
        if any(hostname.endswith(d) for d in allowed_domains):
            return True
    try:
        ip = ipaddress.ip_address(hostname)
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved)
    except ValueError:
        blocked = ["localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "metadata.google"]
        return not any(b in hostname.lower() for b in blocked)


def _mask_config(config: dict) -> dict:
    """Mask sensitive values in plugin config for API responses."""
    return {
        k: ("***" if any(s in k.lower() for s in SENSITIVE_KEYS) else v)
        for k, v in config.items()
    }


class PluginUpdate(BaseModel):
    enabled: bool | None = None
    config: dict | None = None


@router.get("/")
def list_plugins(
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """List all available plugins with their status."""
    configs = {p.name: p for p in db.query(PluginConfig).all()}

    plugins = []
    for name, info in BUILTIN_PLUGINS.items():
        config = configs.get(name)
        plugins.append({
            "name": name,
            "display_name": info["name"],
            "description": info["description"],
            "config_fields": info["config_fields"],
            "enabled": config.enabled if config else False,
            "config": _mask_config(config.config) if config and config.config else {},
        })

    return {"plugins": plugins}


@router.get("/{plugin_name}")
def get_plugin(
    plugin_name: str,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Get a specific plugin configuration."""
    if plugin_name not in BUILTIN_PLUGINS:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found.")

    config = db.query(PluginConfig).filter(PluginConfig.name == plugin_name).first()
    info = BUILTIN_PLUGINS[plugin_name]

    return {
        "name": plugin_name,
        "display_name": info["name"],
        "description": info["description"],
        "config_fields": info["config_fields"],
        "enabled": config.enabled if config else False,
        "config": _mask_config(config.config) if config and config.config else {},
    }


@router.put("/{plugin_name}")
def update_plugin(
    plugin_name: str,
    payload: PluginUpdate,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Update a plugin configuration."""
    if plugin_name not in BUILTIN_PLUGINS:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found.")

    config = db.query(PluginConfig).filter(PluginConfig.name == plugin_name).first()

    if not config:
        config = PluginConfig(name=plugin_name)
        db.add(config)

    if payload.enabled is not None:
        config.enabled = payload.enabled
    if payload.config is not None:
        # SSRF check on webhook URLs
        info = BUILTIN_PLUGINS[plugin_name]
        for key, value in payload.config.items():
            if isinstance(value, str) and ("url" in key.lower() or "webhook" in key.lower()):
                if not _is_safe_url(value, info.get("allowed_domains", [])):
                    raise HTTPException(
                        status_code=422,
                        detail=f"URL for '{key}' points to a private/internal address.",
                    )
        config.config = payload.config

    db.commit()
    db.refresh(config)
    return config.to_dict()


@router.post("/{plugin_name}/test")
def test_plugin(
    plugin_name: str,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Send a test notification through a plugin."""
    if plugin_name not in BUILTIN_PLUGINS:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found.")

    config = db.query(PluginConfig).filter(PluginConfig.name == plugin_name).first()

    if not config or not config.enabled:
        raise HTTPException(status_code=400, detail="Plugin is not enabled.")

    test_payload = {
        "event": "test",
        "message": "This is a test notification from DeepGuard.",
        "case_id": None,
    }

    result = _send_plugin_notification(plugin_name, config.config or {}, test_payload)
    return {"status": "sent" if result["success"] else "failed", "details": result}


def _send_plugin_notification(plugin_name: str, config: dict, payload: dict) -> dict:
    """Send a notification through a plugin. Returns success status."""
    info = BUILTIN_PLUGINS.get(plugin_name, {})
    allowed_domains = info.get("allowed_domains", [])

    if plugin_name in ("slack", "discord", "zapier"):
        url = config.get("webhook_url")
        if not url:
            return {"success": False, "error": "No webhook URL configured."}
        if not _is_safe_url(url, allowed_domains):
            return {"success": False, "error": "URL points to a private/internal address."}
        if plugin_name == "slack":
            body = {"text": f"DeepGuard: {payload.get('message', 'Case update')}"}
        elif plugin_name == "discord":
            body = {"content": f"DeepGuard: {payload.get('message', 'Case update')}"}
        else:
            body = payload
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
            return {"success": True}
        except Exception:
            logger.exception("Plugin notification failed")
            return {"success": False, "error": "Delivery failed."}

    elif plugin_name == "telegram":
        token = config.get("bot_token")
        chat_id = config.get("chat_id")
        if not token or not chat_id:
            return {"success": False, "error": "Bot token or chat ID not configured."}
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        body = {"chat_id": chat_id, "text": f"DeepGuard: {payload.get('message', 'Case update')}"}
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
            return {"success": True}
        except Exception:
            logger.exception("Telegram notification failed")
            return {"success": False, "error": "Delivery failed."}

    return {"success": False, "error": f"Plugin '{plugin_name}' not implemented."}
