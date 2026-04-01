"""Morning Brief v2 pipeline: collect -> draft -> render(agent/self) -> tts -> deliver."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from pathlib import Path
from datetime import datetime

from v2.core.news_weather import build_draft
from v2.core.render_agent import render_via_gateway
from v2.core.tts_edge import synthesize
from v2.core.delivery import send_telegram_audio


@dataclass
class RunResult:
    mode_used: str
    fallback_used: bool
    audio_path: str
    packet_path: str


def build_agent_instruction(cfg: dict[str, Any], draft: str, packet: dict[str, Any]) -> str:
    tpl = cfg.get("render", {}).get("agent_instruction_template", "")
    values = {
        "listener_name": cfg.get("profile", {}).get("listener_name", "朋友"),
        "tone": cfg.get("style", {}).get("tone", "warm_concise"),
        "duration_sec": cfg.get("voice", {}).get("duration_sec", 300),
    }
    try:
        head = tpl.format(**values)
    except Exception:
        head = tpl
    import json
    return f"{head}\n\n【晨報草稿】\n{draft}\n\n【素材包(JSON)】\n{json.dumps(packet, ensure_ascii=False)}"


def render_with_agent(cfg: dict[str, Any], draft: str, packet: dict[str, Any]) -> str:
    return render_via_gateway(build_agent_instruction(cfg, draft, packet))


def render_with_self(cfg: dict[str, Any], draft: str) -> str:
    return draft


def run_pipeline(cfg: dict[str, Any], gnews_key: str, media_dir: str = "/home/ubuntu/.openclaw/media", deliver: bool = True) -> RunResult:
    secrets = {
        "gnews_api_key": gnews_key,
        "newsdata_api_key": __import__('os').getenv("MORNING_BRIEF_NEWSDATA_API_KEY", ""),
    }
    draft, packet = build_draft(cfg, secrets=secrets)
    mode = cfg.get("render", {}).get("mode", "agent")
    fallback = cfg.get("render", {}).get("fallback_mode", "self")

    fallback_used = False
    if mode == "self":
        final_text = render_with_self(cfg, draft)
        mode_used = "self"
    else:
        try:
            final_text = render_with_agent(cfg, draft, packet)
            mode_used = "agent"
        except Exception:
            if fallback != "self":
                raise
            final_text = render_with_self(cfg, draft)
            mode_used = "self"
            fallback_used = True

    date_tag = datetime.now().strftime("%Y%m%d")
    out = Path(media_dir) / f"daily_v2_{date_tag}.mp3"
    packet_path = Path(media_dir) / f"daily_v2_{date_tag}.packet.json"
    packet_path.write_text(__import__('json').dumps(packet, ensure_ascii=False, indent=2), encoding='utf-8')
    voice = cfg.get("voice", {})
    synthesize(
        final_text,
        out,
        voice=voice.get("tts_voice", "zh-TW-HsiaoChenNeural"),
        rate=voice.get("rate", "+0%"),
        pitch=voice.get("pitch", "+0Hz"),
    )

    delivery = cfg.get("delivery", {})
    if deliver and delivery.get("mode") == "telegram":
        chat_id = delivery.get("telegram_chat_id")
        if not chat_id:
            raise RuntimeError("delivery.mode=telegram but telegram_chat_id is missing")
        caption = f"🎙️ {datetime.now().strftime('%Y/%m/%d')} 晨間摘要 v2"
        send_telegram_audio(chat_id, out, caption=caption)

    return RunResult(mode_used=mode_used, fallback_used=fallback_used, audio_path=str(out), packet_path=str(packet_path))
