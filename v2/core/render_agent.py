from __future__ import annotations
import os
import requests


def render_via_gateway(instruction: str, timeout: int = 90) -> str:
    base = os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")
    token = os.getenv("OPENCLAW_GATEWAY_TOKEN", "")
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
