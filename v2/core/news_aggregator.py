from __future__ import annotations
from typing import Any
from .news_adapters import fetch_gnews, fetch_newsdata, fetch_rss

RSS_SOURCES = {
    "bbc": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "reuters": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
    "ap": "https://apnews.com/hub/ap-top-news?output=1"
}


def _norm_key(item: dict) -> str:
    t = (item.get("title") or "").strip().lower()
    u = (item.get("url") or "").strip().lower()
    return f"{t}|{u[:120]}"


def _score(item: dict, source_weight: float = 1.0) -> float:
    score = 0.0
    if item.get("title"): score += 1.0
    if item.get("summary"): score += 0.6
    if item.get("snippet"): score += 0.4
    if item.get("url"): score += 0.3
    if item.get("published_at"): score += 0.2
    return score * source_weight


def collect_topic_candidates(topic_label: str, query: str, cfg: dict[str, Any], secrets: dict[str, str]) -> list[dict]:
    content = cfg.get("content", {})
    enabled = content.get("enabled_sources", ["gnews", "newsdata", "bbc"])
    per_source = int(content.get("max_candidates_per_source", 3))
    min_score = float(content.get("min_quality_score", 1.0))
    weights = content.get("source_priority", {}) or {}

    # topic-level source whitelist
    topic_whitelist = (content.get("topic_source_whitelist", {}) or {}).get(topic_label, [])
    if topic_whitelist:
        enabled = [s for s in enabled if s in topic_whitelist]

    raw = []
    if "gnews" in enabled:
        raw.extend(fetch_gnews(query, secrets.get("gnews_api_key", ""), per_source))
    if "newsdata" in enabled:
        raw.extend(fetch_newsdata(query, secrets.get("newsdata_api_key", ""), per_source))

    for p in ["bbc", "reuters", "ap"]:
        if p in enabled and p in RSS_SOURCES:
            try:
                raw.extend(fetch_rss(RSS_SOURCES[p], p, per_source))
            except Exception:
                pass

    # dedupe + score with source weight
    seen = set()
    out = []
    for item in raw:
        k = _norm_key(item)
        if k in seen:
            continue
        seen.add(k)
        item["topic_tag"] = topic_label
        provider = item.get("provider", "")
        w = float(weights.get(provider, 1.0))
        item["quality_score"] = _score(item, source_weight=w)
        if item["quality_score"] >= min_score:
            out.append(item)

    out.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
    limit_topic = int(content.get("max_candidates_per_topic", 8))
    return out[:limit_topic]
