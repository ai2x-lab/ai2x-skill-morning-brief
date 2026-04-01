from __future__ import annotations
import os
import requests
from pathlib import Path


def send_telegram_audio(chat_id: str, audio_file: Path, caption: str = "") -> dict:
    token = os.getenv("MORNING_BRIEF_TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("missing MORNING_BRIEF_TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendAudio"
    with open(audio_file, "rb") as f:
        r = requests.post(url, data={"chat_id": chat_id, "caption": caption}, files={"audio": f}, timeout=60)
    r.raise_for_status()
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(str(j))
    return j
