from __future__ import annotations
import requests
import xml.etree.ElementTree as ET


def fetch_rss(feed_url: str, provider: str, max_items: int = 3) -> list[dict]:
    try:
        r = requests.get(feed_url, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.text)
    except Exception:
        return []
    items = []
    for item in root.findall('.//item')[:max_items]:
        title = (item.findtext('title') or '').strip()
        desc = (item.findtext('description') or '').strip()
        link = (item.findtext('link') or '').strip()
        pub = (item.findtext('pubDate') or '').strip()
        items.append({
            "title": title,
            "summary": desc[:260],
            "snippet": desc[:400],
            "source": provider.upper(),
            "url": link,
            "published_at": pub,
            "provider": provider,
        })
    return items
