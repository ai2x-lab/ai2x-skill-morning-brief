#!/usr/bin/env python3
"""
Daily Podcast Generator v16
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

# ==== AI Provider 設定 ====
AI_PROVIDERS = {
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
        "ai_provider": "openai",
        "ai_api_key": "YOUR_AI_API_KEY",
        "gnews_api_key": "YOUR_GNEWS_API_KEY",
        "newsdata_api_key": "YOUR_NEWSDATA_API_KEY",
        "telegram_bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
        "telegram_chat_id": "YOUR_TELEGRAM_CHAT_ID"
    }

config = load_config()

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

# ==== AI 翻譯 ====
def translate_to_chinese(text):
    if not text or len(text) < 5:
        return text
    
    api_key = config.get("ai_api_key", "")
    provider_name = config.get("ai_provider", "openai")
    
    if not api_key or api_key == "YOUR_AI_API_KEY":
        print(f"  ⚠️ 未設定 AI API Key，跳過翻譯", file=sys.stderr)
        return text
    
    provider = AI_PROVIDERS.get(provider_name, AI_PROVIDERS["openai"])
    
    prompt = f"""請將以下英文新聞翻譯成繁體中文，保持新聞風格。

規則：
1. 直接翻譯，不要解釋
2. 保持專業術語
3. 人名/地名可保留英文

英文原文：
{text}

中文翻譯："""
    
    try:
        headers = {"Content-Type": "application/json"}
        
        if provider["auth_type"] == "bearer":
            headers["Authorization"] = f"Bearer {api_key}"
        elif provider["auth_type"] == "anthropic":
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        
        if provider["auth_type"] == "anthropic":
            payload = {
                "model": provider["model"],
                "max_tokens": 800,
                "messages": [{"role": "user", "content": prompt}]
            }
        else:
            payload = {
                "model": provider["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800
            }
        
        resp = requests.post(provider["endpoint"], headers=headers, json=payload, timeout=30)
        
        if resp.ok:
            result = resp.json()
            if provider["auth_type"] == "anthropic":
                return result["content"][0]["text"].strip()
            else:
                return result["choices"][0]["message"]["content"].strip()
                
    except Exception as e:
        print(f"  ⚠️ AI 翻譯錯誤: {e}", file=sys.stderr)
    
    return text

# ==== AI 潤飾（TTS 友善版）====
def polish_script(draft):
    api_key = config.get("ai_api_key", "")
    provider_name = config.get("ai_provider", "openai")
    
    if not api_key or api_key == "YOUR_AI_API_KEY":
        print(f"  ⚠️ 未設定 AI API Key，跳過潤飾", file=sys.stderr)
        return draft
    
    provider = AI_PROVIDERS.get(provider_name, AI_PROVIDERS["openai"])
    
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
1. 標題保留，但用更口語的方式表達
2. 新聞之間可以加一句簡短的個人註解
3. 開場和結尾要像朋友說話
4. 每則新聞濃縮成 2-3 句重點精華
5. 保持資訊準確

初稿：
""" + draft

    try:
        print(f"  ✨ AI 潤飾中...", file=sys.stderr)
        
        headers = {"Content-Type": "application/json"}
        
        if provider["auth_type"] == "bearer":
            headers["Authorization"] = f"Bearer {api_key}"
        elif provider["auth_type"] == "anthropic":
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        
        if provider["auth_type"] == "anthropic":
            payload = {
                "model": provider["model"],
                "max_tokens": 2500,
                "messages": [{"role": "user", "content": polish_instructions}]
            }
        else:
            payload = {
                "model": provider["model"],
                "messages": [{"role": "user", "content": polish_instructions}],
                "max_tokens": 2500
            }
        
        resp = requests.post(provider["endpoint"], headers=headers, json=payload, timeout=60)
        
        if resp.ok:
            result = resp.json()
            if provider["auth_type"] == "anthropic":
                result = result["content"][0]["text"].strip()
            else:
                result = result["choices"][0]["message"]["content"].strip()
            
            result = clean_for_tts(result)
            print(f"  ✅ 潤飾完成 ({provider['name']})", file=sys.stderr)
            return result
                
    except Exception as e:
        print(f"  ⚠️ AI 潤飾錯誤: {e}", file=sys.stderr)
    
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
    cmd = f'{EDGE_TTS} --text "{script}" --filepath "{mp3_file}"'
    os.system(cmd + " 2>/dev/null")
    
    if mp3_file.exists() and mp3_file.stat().st_size > 1000:
        print(f"  🎙️ 語音已產生: {mp3_file}", file=sys.stderr)
        return str(mp3_file)
    else:
        print(f"  ❌ 語音產生失敗", file=sys.stderr)
        return None

# ==== 主程式 ====
def main():
    print("=" * 50, file=sys.stderr)
    print(f"🎙️ 每日早報 v16 - {datetime.now().strftime('%Y-%m-%d %H:%M')}", file=sys.stderr)
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
