"""Morning Brief v2 pipeline skeleton: collect -> draft -> render(agent/self) -> tts -> deliver."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class RenderResult:
    text: str
    mode_used: str
    fallback_used: bool = False


def build_agent_instruction(cfg: dict[str, Any], draft: str) -> str:
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
    return f"{head}\n\n【晨報草稿】\n{draft}"


def render_with_agent(cfg: dict[str, Any], draft: str) -> str:
    """Placeholder: Integrator should call host agent runtime using this instruction."""
    instruction = build_agent_instruction(cfg, draft)
    raise RuntimeError("AGENT_RENDER_NOT_WIRED", instruction)


def render_with_self(cfg: dict[str, Any], draft: str) -> str:
    """Placeholder self render: keep draft as-is for now."""
    return draft


def render_text(cfg: dict[str, Any], draft: str) -> RenderResult:
    mode = cfg.get("render", {}).get("mode", "agent")
    fallback = cfg.get("render", {}).get("fallback_mode", "self")

    if mode == "self":
        return RenderResult(text=render_with_self(cfg, draft), mode_used="self")

    try:
        text = render_with_agent(cfg, draft)
        return RenderResult(text=text, mode_used="agent")
    except Exception:
        if fallback == "self":
            return RenderResult(text=render_with_self(cfg, draft), mode_used="self", fallback_used=True)
        raise
