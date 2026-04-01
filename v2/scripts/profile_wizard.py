#!/usr/bin/env python3
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
default_path = BASE / "profiles" / "default.json"
user_path = BASE / "profiles" / "user.json"

cfg = json.loads(default_path.read_text(encoding="utf-8"))

print("=== Morning Brief v2 Configure Wizard ===")

cfg["profile"]["listener_name"] = input(f"listener_name [{cfg['profile']['listener_name']}]: ").strip() or cfg["profile"]["listener_name"]
cfg["profile"]["location"] = input(f"location [{cfg['profile']['location']}]: ").strip() or cfg["profile"]["location"]
cfg["profile"]["locale"] = input(f"locale [{cfg['profile']['locale']}]: ").strip() or cfg["profile"]["locale"]

news_count = input(f"news_count [{cfg['content']['news_count']}]: ").strip()
if news_count.isdigit():
    cfg["content"]["news_count"] = int(news_count)

duration = input(f"voice.duration_sec [{cfg['voice']['duration_sec']}]: ").strip()
if duration.isdigit():
    cfg["voice"]["duration_sec"] = int(duration)

gender = input(f"voice.gender (female/male) [{cfg['voice']['gender']}]: ").strip().lower()
if gender in ("female", "male"):
    cfg["voice"]["gender"] = gender
    cfg["voice"]["tts_voice"] = "zh-TW-HsiaoChenNeural" if gender == "female" else "zh-TW-YunJheNeural"

tone = input(f"style.tone (warm_concise/warm_story/formal_brief) [{cfg['style']['tone']}]: ").strip()
if tone:
    cfg["style"]["tone"] = tone

chat_id = input(f"telegram_chat_id [{cfg['delivery']['telegram_chat_id']}]: ").strip()
if chat_id:
    cfg["delivery"]["telegram_chat_id"] = chat_id

user_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved: {user_path}")
