#!/usr/bin/env python3
"""Load merged profile: default.json -> user.json -> env overrides."""
import json
import os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def deep_merge(a, b):
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_profile():
    default = json.loads((BASE / "profiles" / "default.json").read_text(encoding="utf-8"))
    user_file = BASE / "profiles" / "user.json"
    merged = default
    if user_file.exists():
        user = json.loads(user_file.read_text(encoding="utf-8"))
        merged = deep_merge(default, user)

    # minimal env override (no secrets in repo)
    chat_id = os.getenv("MORNING_BRIEF_TELEGRAM_CHAT_ID")
    if chat_id:
        merged.setdefault("delivery", {})["telegram_chat_id"] = chat_id

    return merged


if __name__ == "__main__":
    print(json.dumps(load_profile(), ensure_ascii=False, indent=2))
