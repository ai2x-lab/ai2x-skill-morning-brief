from __future__ import annotations
import os
import json
from pathlib import Path
import requests


def _resolve_gateway_token() -> str:
    token = os.getenv("OPENCLAW_GATEWAY_TOKEN", "").strip()
    if token:
        return token
    # standard OpenClaw local config fallback
    cfg = Path.home() / ".openclaw" / "openclaw.json"
    if cfg.exists():
        try:
            obj = json.loads(cfg.read_text(encoding="utf-8"))
            return (obj.get("gateway", {}).get("auth", {}).get("token", "") or "").strip()
        except Exception:
            return ""
    return ""


def render_via_gateway(instruction: str, timeout: int = 90) -> str:
    base = os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")
    token = _resolve_gateway_token()
    model = os.getenv("OPENCLAW_MODEL", "gpt-mini")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    r = requests.post(
        f"{base}/v1/chat/completions",
        headers=headers,
        json={"model": model, "messages": [{"role": "user", "content": instruction}], "temperature": 0.6},
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()
