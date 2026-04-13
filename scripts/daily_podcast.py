#!/usr/bin/env python3
"""
Daily Podcast Generator v14b - 晨間語音早報
- GNews API + NewsData.io + BBC RSS
- Open-Meteo 天氣（更準確）
- TTS 友善版本
"""
import requests
import os
import sys
import json
import random
import re
import subprocess
from datetime import datetime
from pathlib import Path

# ==== 路徑設定 ====
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
PODCAST_DIR = Path("/home/ubuntu/clawd/podcast")
MEDIA_DIR = Path("/home/ubuntu/.openclaw/media")
MEMORY_DIR = Path("/home/ubuntu/clawd/memory")
EDGE_TTS = "node /home/ubuntu/.npm-global/lib/node_modules/openclaw/node_modules/node-edge-tts/bin.js"

# ==== Open-Meteo 城市座標 ====
CITY_COORDS = {
    "台北": {"lat": 25.0330, "lon": 121.5654},
    "Taipei": {"lat": 25.0330, "lon": 121.5654},
    "新店": {"lat": 24.9673, "lon": 121.5416},
    "Xindian": {"lat": 24.9673, "lon": 121.5416},
    "台中": {"lat": 24.1477, "lon": 120.6736},
    "Taichung": {"lat": 24.1477, "lon": 120.6736},
    "高雄": {"lat": 22.6273, "lon": 120.3014},
    "Kaohsiung": {"lat": 22.6273, "lon": 120.3014},
    "香港": {"lat": 22.3193, "lon": 114.1694},
    "Hong Kong": {"lat": 22.3193, "lon": 114.1694},
    "東京": {"lat": 35.6762, "lon": 139.6503},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
}

# ==== 載入設定 ====
def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "location": "Xindian,Taiwan",
        "topics": [["國際", "world news"], ["經濟", "economy market"], ["科技", "AI technology"], ["軍事", "military war"], ["能源", "oil energy"]],
        "news_count": 2,
        "sources": ["gnews", "newsdata", "bbc"],
        "pipeline_mode": "self_render",
        "llm_provider": "openai-compatible",
        "llm_base_url": "https://api.openai.com/v1/chat/completions",
        "llm_model": "gpt-4o-mini",
        "llm_api_key": "YOUR_LLM_API_KEY",
        "gnews_api_key": "YOUR_GNEWS_API_KEY",
        "newsdata_api_key": "YOUR_NEWSDATA_API_KEY",
        "telegram_bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
        "telegram_chat_id": "YOUR_TELEGRAM_CHAT_ID"
    }

config = load_config()


def is_agent_delegated_mode():
    return (config.get("pipeline_mode") or "self_render").strip() == "agent_delegated"


def should_translate_in_core():
    # Even in agent_delegated mode, translation can stay in core to keep payload readable.
    return bool(config.get("translate_in_core", True))

# ==== 儲存標題存档 ====
def save_headlines_for_agent(headlines, date_str):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    filename = MEMORY_DIR / f"daily-podcast-{date_str}.md"
    content = f"""# 晨間早報標題存档 - {date_str}

## 標題摘要

{headlines}

---
*此檔案由每日晨報 cron job 自動產生，用於 Agent 後續查閱*
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  📋 標題已存档: {filename}", file=sys.stderr)


def save_brief_payload(payload, date_str):
    PODCAST_DIR.mkdir(parents=True, exist_ok=True)
    payload_file = PODCAST_DIR / f"payload_{date_str.replace('-', '')}.json"
    with open(payload_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"  📦 payload 已存: {payload_file}", file=sys.stderr)

    if is_agent_delegated_mode():
        render_input_file = PODCAST_DIR / f"render_input_{date_str.replace('-', '')}.md"
        lines = [
            f"# Morning Brief Render Input - {date_str}",
            "",
            "請使用本資料進行翻譯與潤飾，產生適合使用者語氣的最終晨報稿。",
            "",
            "## 摘要資料",
            json.dumps(payload, ensure_ascii=False, indent=2),
        ]
        with open(render_input_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  🧩 render input 已存: {render_input_file}", file=sys.stderr)

# ==== Telegram ====
def send_to_telegram(mp3_file, caption=""):
    url = f"https://api.telegram.org/bot{config['telegram_bot_token']}/sendAudio"
    with open(mp3_file, "rb") as f:
        files = {"audio": f}
        data = {"chat_id": config["telegram_chat_id"], "caption": caption}
        resp = requests.post(url, files=files, data=data, timeout=60)
    if resp.ok:
        print(f"  ✅ 已發送到 Telegram", file=sys.stderr)
    else:
        print(f"  ❌ Telegram 錯誤: {resp.text[:200]}", file=sys.stderr)

# ==== 天氣（Open-Meteo）====
def get_weather(location=None):
    """
    使用 Open-Meteo API（免費、不需要 API Key）
    https://open-meteo.com/
    """
    loc = location or config.get("location", "Xindian,Taiwan")

    # 解析地點
    city = loc.split(",")[0].strip()
    coords = CITY_COORDS.get(city)

    if not coords:
        coords = {"lat": 24.9673, "lon": 121.5416}
        print(f"  ⚠️ 未知地點 {city}，使用預設新店", file=sys.stderr)

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "current_weather": True,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "Asia/Taipei"
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        current = data.get("current_weather", {})
        windspeed = round(float(current.get("windspeed", 0)))
        weathercode = int(current.get("weathercode", 0))
        weather_desc = weathercode_to_description(weathercode)

        # 每日預報（今天 index=0）
        daily = data.get("daily", {})
        times = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precip_probs = daily.get("precipitation_probability_max", [])

        temp_max = round(max_temps[0]) if max_temps else "?"
        temp_min = round(min_temps[0]) if min_temps else "?"
        precip_prob = precip_probs[0] if precip_probs else 0

        summary = f"高溫{temp_max}度，低溫{temp_min}度，{weather_desc}，風速{windspeed}公里"
        rain_reminder = f"降雨機率約{precip_prob}%，記得帶雨具！" if precip_prob >= 20 else None

        return summary, rain_reminder

    except Exception as e:
        print(f"  ⚠️ 天氣取得失敗: {e}", file=sys.stderr)
        return "天氣資訊取得失敗", None

def weathercode_to_description(code):
    """將 Open-Meteo 天氣碼轉換成中文描述"""
    weather_map = {
        0: "晴",
        1: "晴時多雲",
        2: "多雲",
        3: "陰天",
        45: "有霧",
        48: "霧凇",
        51: "小毛毛雨",
        53: "中毛毛雨",
        55: "大毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        80: "陣雨",
        81: "中陣雨",
        82: "大陣雨",
        95: "雷暴",
        96: "雷暴伴小冰雹",
        99: "雷暴伴大冰雹",
    }
    return weather_map.get(code, "多雲")


# ==== 民俗行事曆素材（需 lunar-calendar / twcal）====
def get_folk_calendar_brief():
    if not config.get("folk_calendar_enabled", True):
        return ""

    script = "/home/ubuntu/clawd/tools/folk_calendar_brief.py"
    if not os.path.exists(script):
        return ""

    try:
        out = subprocess.check_output(["python3", script], text=True, timeout=10).strip()
        if not out:
            return ""
        return f"\n【民俗行事曆提醒】\n{out}\n"
    except Exception as e:
        print(f"  ⚠️ 民俗行事曆素材取得失敗: {e}", file=sys.stderr)
        return ""

# ==== LLM Provider Config (Provider-agnostic) ====
def get_default_openai_key_from_openclaw():
    try:
        with open(os.path.expanduser("~/.openclaw/openclaw.json"), "r") as f:
            config_oc = json.load(f)
            return config_oc.get("models", {}).get("providers", {}).get("openai", {}).get("apiKey", "")
    except Exception:
        return ""


def get_llm_config():
    provider = (config.get("llm_provider") or "openai").strip()
    base_url = (config.get("llm_base_url") or "https://api.openai.com/v1/chat/completions").strip()
    model = (config.get("llm_model") or "gpt-4o-mini").strip()
    api_key = (config.get("llm_api_key") or "").strip()

    if not api_key:
        # Backward-compatible fallback: reuse openclaw openai key when available
        api_key = get_default_openai_key_from_openclaw()

    return {
        "provider": provider,
        "base_url": base_url,
        "model": model,
        "api_key": api_key,
    }


def llm_chat(prompt: str, max_tokens: int = 800, timeout: int = 60):
    cfg = get_llm_config()
    if not cfg["api_key"]:
        return None

    try:
        resp = requests.post(
            cfg["base_url"],
            headers={"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"},
            json={
                "model": cfg["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        if not resp.ok:
            print(f"  ⚠️ LLM API 錯誤: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
            return None

        data = resp.json()
        return (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip() or None
    except Exception as e:
        print(f"  ⚠️ LLM 呼叫失敗: {e}", file=sys.stderr)
        return None


# ==== AI 翻譯 ====
def translate_to_chinese(text):
    if not text or len(text) < 5:
        return text
    if not should_translate_in_core():
        return text

    prompt = f"""請將以下英文新聞翻譯成繁體中文，保持新聞風格。

規則：
1. 直接翻譯，不要解釋
2. 保持專業術語
3. 人名/地名可保留英文

英文原文：
{text}

中文翻譯："""

    result = llm_chat(prompt, max_tokens=800, timeout=45)
    return result or text


# ==== AI 潤飾（TTS 友善版）====
def polish_script(draft):
    if is_agent_delegated_mode():
        print("  ℹ️ agent_delegated 模式：跳過內建潤飾，交由使用者 Agent 後處理", file=sys.stderr)
        return draft

    if not get_llm_config().get("api_key"):
        print(f"  ⚠️ 無 LLM API key，跳過潤飾", file=sys.stderr)
        return draft

    target_sec = int(config.get("voice_max_duration", 300) or 300)
    # 中文語速粗估：每分鐘 230~260 字，取中間值 245
    target_chars = max(700, int(target_sec / 60 * 245))
    lower = int(target_chars * 0.85)
    upper = int(target_chars * 1.15)

    polish_instructions = f"""
你是一位貼心的私人助理，正在為你的主人準備晨間新聞摘要。

請將以下初稿潤飾成一個「適合語音朗讀」的有溫度版本。

【長度目標】
- 目標時長：約 {target_sec // 60} 分鐘
- 目標字數：大約 {lower} 到 {upper} 字

【嚴格規則】
1. 不要使用任何特殊符號
2. 不要使用 Emoji
3. 不要使用引號
4. 不要使用破折號或省略號
5. 使用全形句號和全形逗號
6. 數字和英文可以直接保留

【內容規則】
1. 標題保留，但用更口語的方式表達
2. 新聞之間可以加一句簡短的個人註解
3. 開場和結尾要像朋友說話
4. 每則新聞濃縮成 2-3 句重點精華
5. 若有民俗行事曆提醒，放在結尾前 1 段，語氣自然
6. 保持資訊準確

初稿：
""" + draft

    print(f"  ✨ AI 潤飾中...", file=sys.stderr)
    result = llm_chat(polish_instructions, max_tokens=2500, timeout=90)
    if result:
        result = clean_for_tts(result)
        print(f"  ✅ 潤飾完成", file=sys.stderr)
        return result
    return draft

# ==== TTS 文字清理 ====
def clean_for_tts(text):
    text = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\n。，！？、；：""''（）【】《》]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ==== GNews 搜尋 ====
def fetch_gnews(category, query, max_results=None):
    count = max_results or config.get("news_count", 2)
    key = config.get("gnews_api_key", "")
    if not key or key == "YOUR_GNEWS_API_KEY":
        return []

    print(f"  🔍 GNews - {category}", file=sys.stderr)
    try:
        url = "https://gnews.io/api/v4/search"
        params = {"q": query, "lang": "en", "max": count, "apikey": key}
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()

        articles = data.get("articles", [])
        results = []
        for art in articles:
            title = art.get("title", "")
            content = art.get("content", "") or art.get("description", "")
            source = art.get("source", {}).get("name", "")

            if title and content:
                content = content.replace("Synopsis\n", "")
                if len(content) > 600:
                    content = content[:600] + "..."

                results.append({
                    "title": title,
                    "content": content,
                    "source": source,
                    "source_name": "GNews"
                })

        print(f"    ✅ 取得 {len(results)} 則", file=sys.stderr)
        return results
    except Exception as e:
        print(f"    ❌ GNews 錯誤: {e}", file=sys.stderr)
        return []

# ==== NewsData 搜尋 ====
def fetch_newsdata(category, query, max_results=None):
    count = max_results or config.get("news_count", 2)
    key = config.get("newsdata_api_key", "")
    if not key or key == "YOUR_NEWSDATA_API_KEY":
        return []

    print(f"  🔍 NewsData - {category}", file=sys.stderr)
    try:
        url = "https://newsdata.io/api/1/news"
        params = {"apikey": key, "q": query, "language": "en", "size": count}
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()

        articles = data.get("results", [])
        results = []
        for art in articles:
            title = art.get("title", "")
            description = art.get("description", "") or art.get("content", "")
            source = art.get("source_name", "")

            if title and description and description != "ONLY AVAILABLE IN PAID PLANS":
                results.append({
                    "title": title,
                    "content": description,
                    "source": source,
                    "source_name": "NewsData"
                })

        print(f"    ✅ 取得 {len(results)} 則", file=sys.stderr)
        return results
    except Exception as e:
        print(f"    ❌ NewsData 錯誤: {e}", file=sys.stderr)
        return []

# ==== BBC RSS 抓取 ====
def fetch_bbc_rss(category, max_results=None):
    count = max_results or config.get("news_count", 2)

    bbc_feeds = {
        "國際": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "科技": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "經濟": "https://feeds.bbci.co.uk/news/business/rss.xml",
    }

    rss_url = bbc_feeds.get(category)
    if not rss_url:
        print(f"  ⚠️ BBC - {category} 無對應 feed", file=sys.stderr)
        return []

    print(f"  🔍 BBC RSS - {category}", file=sys.stderr)
    try:
        resp = requests.get(rss_url, timeout=15)
        items = parse_rss_items(resp.text)

        results = []
        for item in items[:count]:
            title = item.get("title", "")
            description = item.get("description", "")
            if title:
                results.append({
                    "title": title,
                    "content": description or "BBC 新聞",
                    "source": "BBC News",
                    "source_name": "BBC"
                })

        print(f"    ✅ BBC 取得 {len(results)} 則", file=sys.stderr)
        return results
    except Exception as e:
        print(f"    ❌ BBC RSS 錯誤: {e}", file=sys.stderr)
        return []

# ==== 解析 RSS ====
def parse_rss_items(xml_text):
    import re
    items = []
    item_pattern = re.compile(r'<item>(.*?)</item>', re.DOTALL)
    items_xml = item_pattern.findall(xml_text)

    for item_xml in items_xml:
        title = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item_xml)
        if not title:
            title = re.search(r'<title>(.*?)</title>', item_xml)

        desc = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', item_xml)
        if not desc:
            desc = re.search(r'<description>(.*?)</description>', item_xml)

        items.append({
            "title": title.group(1) if title else "",
            "description": desc.group(1) if desc else ""
        })

    return items

# ==== 格式化新聞初稿 ====
def format_news_draft(news_items, category):
    if not news_items:
        return ""

    output = f"\n【{category}】\n"

    for i, item in enumerate(news_items, 1):
        title_cn = translate_to_chinese(item["title"])
        content_cn = translate_to_chinese(item["content"])

        output += f"{i}. {title_cn}。"

        if content_cn:
            sentences = content_cn.split("。")
            first = sentences[0] if sentences else content_cn[:100]
            if len(first) > 150:
                first = first[:150] + "..."
            output += f" {first}。"

        output += "\n"

    return output

# ==== 產生腳本 ====
def generate_script():
    today = datetime.now().strftime("%Y年 %m月 %d日")
    date_str = datetime.now().strftime("%Y-%m-%d")
    weekday = ["一", "二", "三", "四", "五", "六", "日"][datetime.now().weekday()]
    weather_summary, rain_reminder = get_weather()

    folk_calendar = get_folk_calendar_brief()

    listener_name = (config.get("listener_name") or "朋友").strip()
    reminder_line = f"\n{rain_reminder}" if rain_reminder else ""

    draft = f"""Hi {listener_name}，早安！

{today}，星期{weekday}。

今天新店{weather_summary}，出門注意身體。{reminder_line}

以下是今天的早報："""

    topics = config.get("topics", []).copy()
    random.shuffle(topics)

    all_headlines = []
    payload_items = []
    news_count = 0
    sources = config.get("sources", ["gnews"])

    for category, query in topics:
        if news_count >= 10:
            break

        items = []

        if "gnews" in sources:
            items = fetch_gnews(category, query)

        if not items and "newsdata" in sources:
            items = fetch_newsdata(category, query)

        if not items and "bbc" in sources:
            items = fetch_bbc_rss(category)

        if items:
            formatted = format_news_draft(items, category)
            draft += formatted
            news_count += len(items)

            for item in items:
                all_headlines.append(f"- [{category}] {item['title']}（來源：{item.get('source', 'N/A')}）")
                payload_items.append({
                    "category": category,
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "source": item.get("source", "N/A"),
                    "source_name": item.get("source_name", ""),
                })

    if folk_calendar:
        draft += "\n" + folk_calendar

    draft += """
以上就是今天的早報，祝你有美好的一天！

想深入了解哪個議題，隨時告訴我。"""

    PODCAST_DIR.mkdir(parents=True, exist_ok=True)
    draft_file = PODCAST_DIR / f"draft_{date_str.replace('-', '')}.txt"
    with open(draft_file, "w", encoding="utf-8") as f:
        f.write(draft)
    print(f"  📝 初稿已存: {draft_file}", file=sys.stderr)

    headlines_text = "\n".join(all_headlines)
    save_headlines_for_agent(headlines_text, date_str)

    payload = {
        "date": date_str,
        "listener_name": listener_name,
        "location": config.get("location", ""),
        "weather": weather,
        "weekday": weekday,
        "pipeline_mode": config.get("pipeline_mode", "self_render"),
        "folk_calendar": folk_calendar.strip() if folk_calendar else "",
        "items": payload_items,
        "headlines": all_headlines,
    }
    save_brief_payload(payload, date_str)

    polished = polish_script(draft)

    script_file = PODCAST_DIR / f"script_{date_str.replace('-', '')}.txt"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(polished)
    print(f"  ✨ 潤飾後版本已存: {script_file}", file=sys.stderr)

    return polished

# ==== 產生語音 ====
def normalize_tts_text(text: str):
    text = (text or "").replace("（", "，").replace("）", "，")
    text = text.replace("「", "").replace("」", "")
    text = text.replace("\n", " ")
    text = re.sub(r"[\t\r]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[。]{2,}", "。", text)
    return text


def split_tts_chunks(text: str, max_chars: int = 320):
    text = (text or "").strip()
    if len(text) <= max_chars:
        return [text]

    # 優先以段落切，再用句號切，最後硬切
    chunks = []
    for para in [p.strip() for p in text.split("\n") if p.strip()]:
        if len(para) <= max_chars:
            chunks.append(para)
            continue

        sentences = re.split(r'(?<=[。！？.!?])\s*', para)
        buf = ""
        for s in sentences:
            if not s:
                continue
            if len(buf) + len(s) + 1 <= max_chars:
                buf = (buf + " " + s).strip()
            else:
                if buf:
                    chunks.append(buf)
                if len(s) <= max_chars:
                    buf = s
                else:
                    # 句子仍過長時硬切
                    for i in range(0, len(s), max_chars):
                        part = s[i:i + max_chars].strip()
                        if part:
                            chunks.append(part)
                    buf = ""
        if buf:
            chunks.append(buf)

    return [c for c in chunks if c]


def synthesize_edge_tts(text: str, out_file: Path, timeout_sec: int = 60):
    out_file.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "node",
        "/home/ubuntu/.npm-global/lib/node_modules/openclaw/node_modules/node-edge-tts/bin.js",
        "--text", text,
        "--filepath", str(out_file),
        "--timeout", str(timeout_sec),
    ]
    subprocess.run(cmd, check=True, timeout=timeout_sec + 10, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def synthesize_chunk_with_fallback(text: str, out_file: Path, timeout_sec: int, retries: int, depth: int = 0):
    text = normalize_tts_text(text)
    if not text:
        raise RuntimeError("empty tts text")

    for attempt in range(1, retries + 2):
        try:
            synthesize_edge_tts(text, out_file, timeout_sec=timeout_sec)
            if out_file.exists() and out_file.stat().st_size > 1000:
                return [out_file]
        except Exception as e:
            print(f"  ⚠️ TTS 失敗 attempt={attempt} depth={depth}: {e}", file=sys.stderr)

    # 仍失敗就遞迴切小段
    if depth < 2 and len(text) > 80:
        mid = len(text) // 2
        cut = max(text.rfind("。", 0, mid), text.rfind("，", 0, mid), text.rfind(" ", 0, mid))
        if cut <= 0:
            cut = mid
        left = text[:cut].strip()
        right = text[cut:].strip()
        parts = []
        left_file = out_file.with_name(out_file.stem + "_a.mp3")
        right_file = out_file.with_name(out_file.stem + "_b.mp3")
        parts += synthesize_chunk_with_fallback(left, left_file, timeout_sec, retries, depth + 1)
        parts += synthesize_chunk_with_fallback(right, right_file, timeout_sec, retries, depth + 1)
        return parts

    raise RuntimeError("tts chunk failed after retries and split")


def concat_mp3_files(parts, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = subprocess.run(["bash", "-lc", "command -v ffmpeg"], capture_output=True, text=True)
    if ffmpeg.returncode == 0:
        list_file = target.parent / f".{target.stem}_parts.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for p in parts:
                f.write(f"file '{p}'\n")
        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
                "-c", "copy", str(target)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        finally:
            try:
                list_file.unlink(missing_ok=True)
            except Exception:
                pass
    else:
        # fallback: 直接串接（多數播放器可播）
        with open(target, "wb") as out:
            for p in parts:
                with open(p, "rb") as src:
                    out.write(src.read())


def generate_voice(script):
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    mp3_file = MEDIA_DIR / f"daily_{date_str}.mp3"

    timeout_sec = int(config.get("tts_timeout_sec", 60) or 60)
    chunk_chars = int(config.get("tts_chunk_chars", 320) or 320)
    retries = int(config.get("tts_retries", 2) or 2)

    chunks = split_tts_chunks(script, max_chars=chunk_chars)
    part_files = []

    for idx, chunk in enumerate(chunks, start=1):
        part = MEDIA_DIR / f"daily_{date_str}_part{idx:03d}.mp3"
        try:
            produced = synthesize_chunk_with_fallback(chunk, part, timeout_sec=timeout_sec, retries=retries, depth=0)
            part_files.extend(produced)
        except Exception as e:
            print(f"  ❌ TTS 分段最終失敗 part={idx}: {e}", file=sys.stderr)
            for p in part_files:
                p.unlink(missing_ok=True)
            return None

    try:
        concat_mp3_files(part_files, mp3_file)
    except Exception as e:
        print(f"  ❌ TTS 合併失敗: {e}", file=sys.stderr)
        for p in part_files:
            p.unlink(missing_ok=True)
        return None
    finally:
        for p in part_files:
            p.unlink(missing_ok=True)

    if mp3_file.exists() and mp3_file.stat().st_size > 1000:
        print(f"  🎙️ 語音已產生: {mp3_file}", file=sys.stderr)
        return str(mp3_file)

    print(f"  ❌ 語音產生失敗", file=sys.stderr)
    return None

# ==== 主程式 ====
def main():
    print("=" * 50, file=sys.stderr)
    print(f"🎙️ 每日早報 v14b (Open-Meteo 天氣) - {datetime.now().strftime('%Y-%m-%d %H:%M')}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    script = generate_script()
    mp3_file = generate_voice(script)

    if mp3_file:
        caption = f"🎙️ {datetime.now().strftime('%Y/%m/%d')} 晨間摘要"
        send_to_telegram(mp3_file, caption)
        print(f"  ✅ 完成!", file=sys.stderr)
    else:
        print("  ❌ 失敗", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
