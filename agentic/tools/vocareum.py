from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import os

import httpx


@dataclass
class ToolResult:
    ok: bool
    data: Any | None = None
    error: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None


def _build_headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    token = os.getenv("VOCAREUM_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    api_key = os.getenv("VOCAREUM_API_KEY")
    if api_key:
        headers["X-API-Key"] = api_key
    return headers


def _base_url() -> str:
    base = os.getenv("VOCAREUM_BASE_URL", "")
    return base.rstrip("/")


def vocareum_request(method: str, path: str, params: Dict[str, Any] | None = None, json: Dict[str, Any] | None = None, timeout: float = 15.0) -> ToolResult:
    base = _base_url()
    if not base:
        return ToolResult(ok=False, error={"code": "NO_BASE_URL", "message": "VOCAREUM_BASE_URL not set"})
    url = f"{base}/{path.lstrip('/')}"
    try:
        with httpx.Client(timeout=timeout, headers=_build_headers()) as client:
            resp = client.request(method=method.upper(), url=url, params=params, json=json)
            ct = resp.headers.get("content-type", "")
            data = resp.json() if "json" in ct or resp.text.startswith("{") else {"text": resp.text}
            if resp.status_code >= 200 and resp.status_code < 300:
                return ToolResult(ok=True, data=data, status_code=resp.status_code)
            return ToolResult(ok=False, data=data, status_code=resp.status_code, error={"code": "HTTP_ERROR", "message": resp.text})
    except Exception as e:
        return ToolResult(ok=False, error={"code": "EXCEPTION", "message": str(e)})


def escalate_to_vocareum(ticket_id: str, reason: str, payload: Dict[str, Any] | None = None) -> ToolResult:
    path = os.getenv("VOCAREUM_ESCALATION_PATH", "/api/escalations")
    body = {
        "ticket_id": ticket_id,
        "reason": reason,
    }
    if payload:
        body.update({"payload": payload})
    return vocareum_request("POST", path, json=body)
