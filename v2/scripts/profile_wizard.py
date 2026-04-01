#!/usr/bin/env python3
"""Generate v2 profiles/user.json interactively (safe customizable layer)."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
default_path = BASE / "profiles" / "default.json"
user_path = BASE / "profiles" / "user.json"

cfg = json.loads(default_path.read_text(encoding="utf-8"))

print("=== Morning Brief v2 Profile Wizard ===")
name = input(f"listener_name [{cfg['identity']['listener_name']}]: ").strip() or cfg['identity']['listener_name']
loc = input(f"location [{cfg['identity']['location']}]: ").strip() or cfg['identity']['location']
locale = input(f"locale [{cfg['identity']['locale']}]: ").strip() or cfg['identity']['locale']
dur = input(f"voice_max_duration [{cfg['delivery']['voice_max_duration']}]: ").strip()

cfg['identity']['listener_name'] = name
cfg['identity']['location'] = loc
cfg['identity']['locale'] = locale
if dur.isdigit():
    cfg['delivery']['voice_max_duration'] = int(dur)

user_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved: {user_path}")
