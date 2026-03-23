#!/usr/bin/env python3
"""
Daily Podcast Generator v12 - 晨間語音早報
- TTS 友善版本（無特殊符號）
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

# ==== 載入設定 ====
def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "location": "Xindian,Taiwan",
        "topics": [["國際", "world news"], ["經濟", "economy market"], ["科技", "AI technology"], ["軍事", "military war"], ["能源", "oil energy"]],
        "news_count": 2,
        "sources": ["gnews", "newsdata"],
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
    return filename

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

# ==== 天氣 ====
def get_weather(location=None):
    loc = location or config.get("location", "Xindian,Taiwan")
    try:
        url = f"https://wttr.in/{loc.replace(',', ',')}?format=j1"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        curr = data.get("current_condition", [{}])[0]
        temp = curr.get("temp_C", "?")
        desc = curr.get("weatherDesc", [{}])[0].get("value", "未知")
        feels = curr.get("FeelsLikeC", "?")
        humidity = curr.get("humidity", "?")
        wind = curr.get("windspeedKmph", "?")
        return f"{temp}度，{desc}，體感{feels}度，濕度{humidity}%，風速{wind}公里"
    except Exception as e:
        print(f"Weather error: {e}", file=sys.stderr)
        return "天氣資訊取得失敗"

# ==== OpenAI API Key ====
def get_openai_key():
    try:
        with open(os.path.expanduser("~/.openclaw/openclaw.json"), "r") as f:
            config_oc = json.load(f)
            return config_oc.get("models", {}).get("providers", {}).get("openai", {}).get("apiKey", "")
    except:
        return ""

# ==== AI 翻譯 ====
def translate_to_chinese(text):
    if not text or len(text) < 5:
        return text
    api_key = get_openai_key()
    if not api_key:
        return text
    
    prompt = f"""請將以下英文新聞翻譯成繁體中文，保持新聞風格。

規則：
1. 直接翻譯，不要解釋
2. 保持專業術語
3. 人名/地名可保留英文

英文原文：
{text}

中文翻譯："""
    
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 800},
            timeout=30
        )
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  ⚠️ 翻譯錯誤: {e}", file=sys.stderr)
    return text

# ==== AI 潤飾（TTS 友善版）====
def polish_script(draft):
    api_key = get_openai_key()
    if not api_key:
        print(f"  ⚠️ 無 API key，跳過潤飾", file=sys.stderr)
        return draft
    
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

【舉例】
- 好：早安，希望你今天有個愉快的開始
- 不好：早安！希望你今天有個愉快的開始～

初稿：
""" + draft

    try:
        print(f"  ✨ AI 潤飾中...", file=sys.stderr)
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": polish_instructions}], "max_tokens": 2500},
            timeout=60
        )
        if resp.ok:
            result = resp.json()["choices"][0]["message"]["content"].strip()
            result = clean_for_tts(result)
            print(f"  ✅ 潤飾完成", file=sys.stderr)
            return result
    except Exception as e:
        print(f"  ⚠️ 潤飾錯誤: {e}", file=sys.stderr)
    return draft

# ==== TTS 文字清理 ====
def clean_for_tts(text):
    """清理文字，移除 TTS 會唸錯的符號"""
    # 移除所有特殊符號（保留中文和基本英數）
    text = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\n。，！？、；：""''（）【】《》]', '', text)
    # 移除多餘空白
    text = re.sub(r'\s+', ' ', text)
    # 移除行首行尾空白
    text = text.strip()
    return text

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
    for category, query in topics:
        if news_count >= 10:
            break
        
        items = fetch_gnews(category, query)
        if not items and "newsdata" in config.get("sources", []):
            items = fetch_newsdata(category, query)
        
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
    print(f"🎙️ 每日早報 v12 (TTS 友善版) - {datetime.now().strftime('%Y-%m-%d %H:%M')}", file=sys.stderr)
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
