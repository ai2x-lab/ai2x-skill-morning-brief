from __future__ import annotations
import requests


def fetch_newsdata(query: str, api_key: str, max_items: int = 3) -> list[dict]:
    if not api_key:
        return []
    r = requests.get(
        "https://newsdata.io/api/1/news",
        params={"apikey": api_key, "q": query, "language": "en", "size": max_items},
        timeout=15,
    )
    r.raise_for_status()
    out = []
    for a in r.json().get("results", [])[:max_items]:
        out.append({
            "title": a.get("title", ""),
            "summary": a.get("description", "") or "",
            "snippet": (a.get("content", "") or "")[:400],
            "source": a.get("source_id", "NewsData"),
            "url": a.get("link", ""),
            "published_at": a.get("pubDate", ""),
            "provider": "newsdata",
        })
    return out
