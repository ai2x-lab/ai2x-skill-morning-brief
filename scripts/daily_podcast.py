#!/usr/bin/env python3
"""
Daily Podcast Generator v18
AI-powered morning briefing skill for OpenClaw agents.

Creator: Microsense Vision Co., Ltd. | Allan@msviso.com
License: MIT
https://github.com/ai2x-lab/ai2x-skill-morning-brief
"""
import requests
import os
import sys
import json
import random
import re
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

# ==== 路徑設定 ====
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
PODCAST_DIR = Path("/home/ubuntu/clawd/podcast")
MEDIA_DIR = Path("/home/ubuntu/.openclaw/media")
MEMORY_DIR = Path("/home/ubuntu/clawd/memory")
EDGE_TTS_CANDIDATES = [
    ["node", "/home/ubuntu/.npm-global/lib/node_modules/openclaw/node_modules/node-edge-tts/bin.js"],
    ["node-edge-tts"],
    ["npx", "-y", "node-edge-tts"],
]

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

# ==== AI Provider 設定 ====
AI_PROVIDERS = {
    "openclaw_local": {
        "name": "OpenClaw Local",
        "model": "openai/gpt-4o-mini",
        "endpoint": None,
        "auth_type": "openclaw",
    },
    "openai": {
        "name": "OpenAI",
        "model": "gpt-4o-mini",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "auth_type": "bearer",
    },
    "minimax": {
        "name": "MiniMax",
        "model": "MiniMax-M2.1",
        "endpoint": "https://api.minimax.chat/v1/text/chatcompletion_v2",
        "auth_type": "bearer",
    },
    "anthropic": {
        "name": "Anthropic",
        "model": "claude-3-haiku-20240307",
        "endpoint": "https://api.anthropic.com/v1/messages",
        "auth_type": "anthropic",
    },
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
        "ai_provider": "auto",
        "ai_fallback_providers": ["openclaw_local", "minimax", "openai", "anthropic"],
        "ai_model": "openai/gpt-4o-mini",
        "ai_use_agent_fallback": True,
        "ai_agent_id": "lumi",
        "ai_api_key": "",
        "gnews_api_key": "YOUR_GNEWS_API_KEY",
        "newsdata_api_key": "YOUR_NEWSDATA_API_KEY",
        "delivery_mode": "none",
        "telegram_bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
        "telegram_chat_id": "YOUR_TELEGRAM_CHAT_ID"
    }

config = load_config()

# v17 migration defaults (backward compatible)
config.setdefault("ai_provider", "auto")
config.setdefault("ai_fallback_providers", ["openclaw_local", "minimax", "openai", "anthropic"])
config.setdefault("ai_model", "openai/gpt-4o-mini")
config.setdefault("ai_use_agent_fallback", True)
config.setdefault("ai_agent_id", "lumi")
if config.get("ai_api_key") == "YOUR_AI_API_KEY":
    config["ai_api_key"] = ""
config.setdefault("delivery_mode", "none")

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

# ==== Telegram ====
def send_to_telegram(mp3_file, caption=""):
    token = config.get("telegram_bot_token", "")
    chat_id = config.get("telegram_chat_id", "")
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN" or not chat_id or chat_id == "YOUR_TELEGRAM_CHAT_ID":
        print("  ⚠️ Telegram 未設定，略過傳送", file=sys.stderr)
        return False

    url = f"https://api.telegram.org/bot{token}/sendAudio"
    with open(mp3_file, "rb") as f:
        files = {"audio": f}
        data = {"chat_id": chat_id, "caption": caption}
        resp = requests.post(url, files=files, data=data, timeout=60)
    if resp.ok:
        print(f"  ✅ 已發送到 Telegram", file=sys.stderr)
        return True

    msg = resp.text[:200]
    print(f"  ❌ Telegram 錯誤: {msg}", file=sys.stderr)
    if "chat not found" in msg.lower():
        print("  💡 請先讓使用者在 Telegram 主動對 Bot 發送 /start（或任一訊息）以啟用 chat。", file=sys.stderr)
    return False

# ==== 天氣（Open-Meteo）====
def get_weather(location=None):
    loc = location or config.get("location", "Xindian,Taiwan")
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
            "hourly": "relativehumidity_2m",
            "timezone": "Asia/Taipei"
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        current = data.get("current_weather", {})
        temp = float(current.get("temperature", 0))
        windspeed = float(current.get("windspeed", 0))
        weathercode = int(current.get("weathercode", 0))
        
        weather_desc = weathercode_to_description(weathercode)
        
        hourly = data.get("hourly", {})
        humidity_data = hourly.get("relativehumidity_2m", []) if hourly else []
        humidity = humidity_data[0] if humidity_data else None
        
        temp_rounded = round(temp)
        windspeed_rounded = round(windspeed)
        
        result = f"{temp_rounded}度，{weather_desc}，風速{windspeed_rounded}公里"
        if humidity is not None:
            result += f"，濕度{round(humidity)}%"
        
        return result
        
    except Exception as e:
        print(f"  ⚠️ 天氣取得失敗: {e}", file=sys.stderr)
        return "天氣資訊取得失敗"

def weathercode_to_description(code):
    weather_map = {
        0: "晴", 1: "晴時多雲", 2: "多雲", 3: "陰天",
        45: "有霧", 48: "霧凇",
        51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
        61: "小雨", 63: "中雨", 65: "大雨",
        71: "小雪", 73: "中雪", 75: "大雪",
        80: "陣雨", 81: "中陣雨", 82: "大陣雨",
        95: "雷暴", 96: "雷暴伴小冰雹", 99: "雷暴伴大冰雹",
    }
    return weather_map.get(code, "多雲")


def load_openclaw_gateway_config():
    conf = Path.home() / ".openclaw" / "openclaw.json"
    if not conf.exists():
        return None
    try:
        data = json.loads(conf.read_text(encoding="utf-8"))
        gateway = data.get("gateway", {})
        port = gateway.get("port", 18789)
        token = gateway.get("auth", {}).get("token", "")
        if not token:
            return None
        return {"port": port, "token": token}
    except Exception:
        return None


def call_agent_ai(prompt):
    agent_id = config.get("ai_agent_id", "lumi")
    try:
        proc = subprocess.run(
            [
                "openclaw", "agent",
                "--agent", str(agent_id),
                "--message", prompt,
                "--json",
                "--thinking", "off"
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            print(f"  ⚠️ agent fallback 失敗: returncode={proc.returncode}", file=sys.stderr)
            return None
        data = json.loads(proc.stdout)
        payloads = (((data or {}).get("result") or {}).get("payloads") or [])
        if payloads and isinstance(payloads[0], dict):
            text = (payloads[0].get("text") or "").strip()
            if text:
                print(f"  ✅ agent fallback 成功（agent={agent_id}）", file=sys.stderr)
                return text
    except Exception as e:
        print(f"  ⚠️ agent fallback 例外: {e}", file=sys.stderr)
    return None


def call_ai_model(prompt, max_tokens=800):
    provider_name = config.get("ai_provider", "auto")

    # Quick hint for common misconfiguration
    api_key = (config.get("ai_api_key", "") or "").strip()
    if provider_name in ("minimax", "openai", "anthropic") and (not api_key or api_key == "YOUR_AI_API_KEY"):
        print(f"  ⚠️ {provider_name} 模式未設定 ai_api_key", file=sys.stderr)

    # Build candidate chain
    if provider_name == "auto":
        candidates = config.get("ai_fallback_providers", ["openclaw_local", "minimax", "openai", "anthropic"])
    else:
        candidates = [provider_name]
        if provider_name != "openclaw_local":
            candidates.append("openclaw_local")

    for candidate in candidates:
        p = AI_PROVIDERS.get(candidate)
        if not p:
            continue

        try:
            # OpenClaw local gateway mode (no external API key needed)
            if p["auth_type"] == "openclaw":
                gw = load_openclaw_gateway_config()
                if not gw:
                    continue

                headers = {
                    "Authorization": f"Bearer {gw['token']}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": config.get("ai_model", p["model"]),
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens
                }
                resp = requests.post(
                    f"http://127.0.0.1:{gw['port']}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )

                # Some environments return dashboard HTML; treat as unavailable
                content_type = (resp.headers.get("content-type") or "").lower()
                if not resp.ok or "application/json" not in content_type:
                    print(f"  ⚠️ local gateway 非 JSON 回應，跳過（status={resp.status_code}）", file=sys.stderr)
                    continue

                data = resp.json()
                choices = data.get("choices") if isinstance(data, dict) else None
                if choices and choices[0].get("message", {}).get("content"):
                    return choices[0]["message"]["content"].strip()

                print("  ⚠️ local gateway JSON 結構不符，跳過", file=sys.stderr)
                continue

            # External provider mode
            api_key = config.get("ai_api_key", "")
            if not api_key:
                continue

            headers = {"Content-Type": "application/json"}
            if p["auth_type"] == "bearer":
                headers["Authorization"] = f"Bearer {api_key}"
            elif p["auth_type"] == "anthropic":
                headers["x-api-key"] = api_key
                headers["anthropic-version"] = "2023-06-01"

            if p["auth_type"] == "anthropic":
                payload = {
                    "model": p["model"],
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                }
            else:
                payload = {
                    "model": p["model"],
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens
                }

            resp = requests.post(p["endpoint"], headers=headers, json=payload, timeout=60)
            if resp.ok:
                result = resp.json()
                if p["auth_type"] == "anthropic":
                    text = result.get("content", [{}])[0].get("text", "").strip()
                else:
                    text = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if text:
                    return text

        except Exception as e:
            print(f"  ⚠️ AI 呼叫失敗 ({candidate}): {e}", file=sys.stderr)

    if config.get("ai_use_agent_fallback", True):
        print("  🔁 嘗試 agent fallback（無 key 方案）...", file=sys.stderr)
        return call_agent_ai(prompt)

    return None

# ==== AI 翻譯 ====
def translate_to_chinese(text):
    if not text or len(text) < 5:
        return text

    prompt = f"""請將以下英文新聞翻譯成繁體中文，保持新聞風格。

規則：
1. 直接翻譯，不要解釋
2. 保持專業術語
3. 人名/地名可保留英文

英文原文：
{text}

中文翻譯："""

    result = call_ai_model(prompt, max_tokens=800)
    if result:
        return result

    print("  ⚠️ AI 翻譯不可用，保留原文", file=sys.stderr)
    return text

# ==== AI 潤飾（TTS 友善版）====
def polish_script(draft):
    polish_instructions = """
你是一位貼心的私人助理，正在為你的主人準備晨間新聞摘要。

請將以下初稿潤飾成一個「適合語音朗讀」的有溫度版本：

【嚴格規則】
1. 不要使用任何特殊符號
2. 不要使用 Emoji
3. 不要使用引號
4. 不要使用破折號或省略號
5. 使用全形句號和全形逗號
6. 數字和英文可以直接保留

【內容規則】
1. 先給三行重點摘要：國際、科技、經濟或能源（有資料才寫）
2. 標題保留，但用更口語的方式表達
3. 新聞之間可以加一句簡短的個人註解
4. 每則新聞濃縮成 2-3 句重點精華
5. 保持資訊準確
6. 最後加一段今天行動建議（不超過 2 句）

初稿：
""" + draft

    print("  ✨ AI 潤飾中...", file=sys.stderr)
    result = call_ai_model(polish_instructions, max_tokens=2500)
    if result:
        result = clean_for_tts(result)
        # 品質防呆：過短就回退原稿
        if len(result) >= max(180, len(draft) // 3):
            print("  ✅ 潤飾完成", file=sys.stderr)
            return result
        print("  ⚠️ 潤飾結果過短，使用原稿", file=sys.stderr)

    print("  ⚠️ AI 潤飾不可用，使用原稿", file=sys.stderr)
    return draft

# ==== TTS 文字清理 ====
def clean_for_tts(text):
    text = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\n。，！？、；：""''（）【】《》]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def resolve_tts_command():
    for cmd in EDGE_TTS_CANDIDATES:
        exe = cmd[0]
        if exe == "node":
            if len(cmd) > 1 and Path(cmd[1]).exists():
                return cmd
        else:
            if shutil.which(exe):
                return cmd
    return None


def ensure_tts_command():
    cmd = resolve_tts_command()
    if cmd:
        return cmd

    print("  ⚠️ 未找到 TTS 指令，嘗試自動安裝 node-edge-tts...", file=sys.stderr)
    try:
        subprocess.run(["npm", "i", "-g", "node-edge-tts"], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except Exception as e:
        print(f"  ⚠️ 自動安裝失敗: {e}", file=sys.stderr)

    cmd = resolve_tts_command()
    if cmd:
        print("  ✅ TTS 已可用", file=sys.stderr)
        return cmd

    print("  ❌ TTS 仍不可用。請先安裝：npm i -g node-edge-tts", file=sys.stderr)
    return None

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
    weather = get_weather()
    
    draft = f"""Hi Weichien，早安！

今天新店的氣溫是{weather}，記得多穿點出門。

{today}，星期{weekday}，以下是今天的早報："""
    
    topics = config.get("topics", []).copy()
    random.shuffle(topics)
    
    all_headlines = []
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
    
    polished = polish_script(draft)
    
    script_file = PODCAST_DIR / f"script_{date_str.replace('-', '')}.txt"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(polished)
    print(f"  ✨ 潤飾後版本已存: {script_file}", file=sys.stderr)
    
    return polished

# ==== 產生語音 ====
def generate_voice(script):
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    mp3_file = MEDIA_DIR / f"daily_{date_str}.mp3"

    tts_cmd = ensure_tts_command()
    if not tts_cmd:
        return None

    cmd = tts_cmd + ["--text", script, "--filepath", str(mp3_file)]
    try:
        proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            print(f"  ❌ TTS 執行失敗 (code={proc.returncode})", file=sys.stderr)
            if proc.stderr:
                print(f"  stderr: {proc.stderr[:300]}", file=sys.stderr)
    except Exception as e:
        print(f"  ❌ TTS 執行例外: {e}", file=sys.stderr)
        return None

    if mp3_file.exists() and mp3_file.stat().st_size > 1000:
        print(f"  🎙️ 語音已產生: {mp3_file}", file=sys.stderr)
        return str(mp3_file)

    print(f"  ❌ 語音產生失敗", file=sys.stderr)
    return None

# ==== 主程式 ====
def main():
    print("=" * 50, file=sys.stderr)
    print(f"🎙️ 每日早報 v18 - {datetime.now().strftime('%Y-%m-%d %H:%M')}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    # startup diagnostics
    provider = config.get("ai_provider", "auto")
    api_key = (config.get("ai_api_key", "") or "").strip()
    key_set = bool(api_key and api_key != "YOUR_AI_API_KEY")
    delivery_mode = config.get("delivery_mode", "none")
    print(f"  🤖 AI provider: {provider}", file=sys.stderr)
    print(f"  📦 delivery_mode: {delivery_mode}", file=sys.stderr)
    if provider != "openclaw_local" and not key_set:
        print("  ⚠️ 未設定 ai_api_key：翻譯與潤飾可能不可用（除非 local gateway 可用）", file=sys.stderr)

    script = generate_script()
    mp3_file = generate_voice(script)

    if mp3_file:
        caption = f"🎙️ {datetime.now().strftime('%Y/%m/%d')} 晨間摘要"
        delivered = False

        if delivery_mode == "telegram":
            delivered = send_to_telegram(mp3_file, caption)
        elif delivery_mode == "stdout":
            print(f"AUDIO_FILE={mp3_file}")
            delivered = True
        else:
            print("  ℹ️ delivery_mode=none：僅產生檔案，不主動推播", file=sys.stderr)

        print(f"  ✅ 完成! delivered={delivered}", file=sys.stderr)
    else:
        print("  ❌ 失敗", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
