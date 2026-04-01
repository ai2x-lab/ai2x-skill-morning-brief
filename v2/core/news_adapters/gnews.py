from __future__ import annotations
import requests


def fetch_gnews(query: str, api_key: str, max_items: int = 3) -> list[dict]:
    if not api_key:
        return []
    r = requests.get(
        "https://gnews.io/api/v4/search",
        params={"q": query, "lang": "en", "max": max_items, "apikey": api_key},
        timeout=15,
    )
    r.raise_for_status()
    out = []
    for a in r.json().get("articles", [])[:max_items]:
        out.append({
            "title": a.get("title", ""),
            "summary": a.get("description", "") or "",
            "snippet": (a.get("content", "") or "")[:400],
            "source": a.get("source", {}).get("name", "GNews"),
            "url": a.get("url", ""),
            "published_at": a.get("publishedAt", ""),
            "provider": "gnews",
        })
    return out
