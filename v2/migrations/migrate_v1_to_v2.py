#!/usr/bin/env python3
"""Convert legacy scripts/config.json into v2 profiles/user.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
legacy = ROOT / "scripts" / "config.json"
default = ROOT / "v2" / "profiles" / "default.json"
out = ROOT / "v2" / "profiles" / "user.json"

if not legacy.exists():
    print(f"legacy config not found: {legacy}")
    raise SystemExit(1)

base = json.loads(default.read_text(encoding="utf-8"))
old = json.loads(legacy.read_text(encoding="utf-8"))

base["identity"]["listener_name"] = old.get("listener_name", base["identity"]["listener_name"])
base["identity"]["location"] = old.get("location", base["identity"]["location"])
base["delivery"]["voice_max_duration"] = old.get("voice_max_duration", base["delivery"]["voice_max_duration"])
base["delivery"]["telegram_chat_id"] = old.get("telegram_chat_id", "")
base["content"]["topics"] = old.get("topics", base["content"]["topics"])
base["content"]["news_count"] = old.get("news_count", base["content"]["news_count"])
base["content"]["sources"] = old.get("sources", base["content"]["sources"])

out.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"migrated -> {out}")
