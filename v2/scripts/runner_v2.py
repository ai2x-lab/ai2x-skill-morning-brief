#!/usr/bin/env python3
"""v2 runner: execute full pipeline with agent-first render and self fallback."""
import json
import os
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v2.scripts.load_profile import load_profile
from v2.core.pipeline import run_pipeline


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Generate audio but do not deliver")
    args = ap.parse_args()

    cfg = load_profile()
    gnews_key = os.getenv("MORNING_BRIEF_GNEWS_API_KEY", "")
    res = run_pipeline(cfg, gnews_key=gnews_key, deliver=not args.dry_run)
    print(json.dumps({
        "ok": True,
        "mode_used": res.mode_used,
        "fallback_used": res.fallback_used,
        "audio_path": res.audio_path,
        "packet_path": res.packet_path,
        "delivery_mode": cfg.get("delivery", {}).get("mode", "none"),
        "dry_run": args.dry_run
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
