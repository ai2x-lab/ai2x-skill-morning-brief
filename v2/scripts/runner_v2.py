#!/usr/bin/env python3
"""v2 runner skeleton (design-first): loads profile and simulates render decision."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v2.scripts.load_profile import load_profile
from v2.core.pipeline import render_text


def main():
    cfg = load_profile()
    draft = "這裡是晨報草稿（示意）。"
    result = render_text(cfg, draft)
    out = {
        "mode_used": result.mode_used,
        "fallback_used": result.fallback_used,
        "text": result.text[:80]
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
