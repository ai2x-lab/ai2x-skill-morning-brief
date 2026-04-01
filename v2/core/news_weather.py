from __future__ import annotations
import random
import requests

CITY_COORDS = {
    "Xindian": {"lat": 24.9673, "lon": 121.5416},
    "Taipei": {"lat": 25.0330, "lon": 121.5654},
    "Taichung": {"lat": 24.1477, "lon": 120.6736},
    "Kaohsiung": {"lat": 22.6273, "lon": 120.3014},
}


def weather_desc(code: int) -> str:
    m = {0: "晴", 1: "晴時多雲", 2: "多雲", 3: "陰天", 61: "小雨", 63: "中雨", 65: "大雨", 80: "陣雨", 95: "雷暴"}
    return m.get(code, "多雲")


def get_weather(location: str) -> str:
    city = (location or "Xindian,Taiwan").split(",")[0].strip()
    coords = CITY_COORDS.get(city, CITY_COORDS["Xindian"])
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "current_weather": True,
            "timezone": "Asia/Taipei",
        },
        timeout=10,
    )
    r.raise_for_status()
    cur = r.json().get("current_weather", {})
    t = round(float(cur.get("temperature", 0)))
    w = weather_desc(int(cur.get("weathercode", 0)))
    return f"{t}度，{w}"


def fetch_gnews(query: str, api_key: str, max_items: int = 2) -> list[dict]:
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
        out.append({"title": a.get("title", ""), "summary": a.get("description", ""), "source": a.get("source", {}).get("name", "")})
    return out


def build_draft(cfg: dict, gnews_key: str) -> str:
    profile = cfg.get("profile", {})
    content = cfg.get("content", {})
    topics = content.get("topics", [])[:]
    random.shuffle(topics)
    news_count = int(content.get("news_count", 2))

    weather = get_weather(profile.get("location", "Xindian,Taiwan"))
    lines = [
        f"早安 {profile.get('listener_name','朋友')}，",
        f"今天 {profile.get('location','Xindian,Taiwan')} 天氣 {weather}。",
        "以下是今日晨報重點：",
    ]

    for label, q in topics[:5]:
        items = fetch_gnews(q, gnews_key, max_items=news_count)
        if not items:
            continue
        lines.append(f"【{label}】")
        for i, it in enumerate(items, 1):
            title = (it.get("title") or "").strip()
            summary = (it.get("summary") or "").strip()
            lines.append(f"{i}. {title}。{summary}")

    lines.append("以上是今天晨報，祝你今天順利。")
    return "\n".join(lines)
