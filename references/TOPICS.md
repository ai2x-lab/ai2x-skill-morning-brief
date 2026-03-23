# 主題範例指南

## 新聞來源說明

| 來源 | 需要 API Key | 內容品質 | 說明 |
|------|-------------|----------|------|
| **GNews** | ✅ 需要 | ⭐⭐⭐ | 有 3000+ 字摘要內容 |
| **NewsData** | ✅ 需要 | ⭐⭐ | 只有描述，付費才有全文 |
| **BBC RSS** | ❌ 不需要 | ⭐⭐⭐ | 免費，標題+描述，無需申請 |

### 測試經驗（2026-03 實測）

**GNews API**：
- 有 `content` 欄位，最多 3965 字
- 經 AI 潤飾後內容豐富
- 免費額度 100次/天
- 12小時延遲（付費可移除）

**NewsData.io**：
- 免費版 `content` 欄位顯示「ONLY AVAILABLE IN PAID PLANS」
- 只有 `description` 可用（約 100-150 字）
- 適合當備用來源

**BBC RSS**：
- 完全免費，不需要 API Key
- RSS URL 直接可用
- 描述欄位比 Google News RSS 豐富
- 建議作為「國際」或「英國/歐洲」新聞的備用來源

## sources 設定

```json
{
  "sources": ["gnews", "newsdata", "bbc"]
}
```

順序代表優先順序：
1. `gnews` - 主要來源（內容最完整）
2. `newsdata` - GNews 失敗時的備用
3. `bbc` - 最後備用（免費但內容較少）

如只用 BBC RSS：
```json
{
  "sources": ["bbc"]
}
```

## BBC RSS URL 對照

| 分類 | RSS URL |
|------|---------|
| 國際 | `https://feeds.bbci.co.uk/news/world/rss.xml` |
| 科技 | `https://feeds.bbci.co.uk/news/technology/rss.xml` |
| 經濟 | `https://feeds.bbci.co.uk/news/business/rss.xml` |
| 英國 | `https://feeds.bbci.co.uk/news/uk/rss.xml` |

## 主題關鍵字

### 新聞類
| 分類 | 關鍵字 | 說明 |
|------|--------|------|
| 國際 | `world news` | 全球重大新聞 |
| 國際 | `geopolitics` | 地緣政治 |
| 國際 | `Europe news` | 歐洲新聞 |
| 經濟 | `economy market` | 總體經濟 |
| 經濟 | `stock market` | 股市 |
| 經濟 | `cryptocurrency bitcoin` | 加密貨幣 |
| 科技 | `AI technology` | AI 科技 |
| 科技 | `Apple OR Google OR Microsoft` | 科技巨頭 |
| 軍事 | `military war` | 軍事戰爭 |
| 軍事 | `defense technology` | 國防科技 |
| 能源 | `oil energy` | 石油能源 |
| 政治 | `US politics` | 美國政治 |
| 政治 | `China Taiwan` | 中國台灣 |

### 體育類
| 分類 | 關鍵字 |
|------|--------|
| NBA | `NBA Lakers` |
| NBA | `NBA Warriors Curry` |
| 籃球 | `basketball` |
| 足球 | `Premier League soccer` |
| 網球 | `tennis Grand Slam` |

### 藝術文化類
| 分類 | 關鍵字 |
|------|--------|
| 藝術 | `art exhibition museum` |
| 電影 | `Hollywood movie` |
| 音樂 | `music concert` |
| 設計 | `design architecture` |
| 遊戲 | `video game esports` |

## 主題設定範例

### 科技愛好者
```json
[
  ["AI 科技", "artificial intelligence"],
  ["科技巨頭", "Apple Google Microsoft"],
  ["新創科技", "tech startup"],
  ["半導體", "semiconductor chip"],
  ["遊戲電競", "gaming esports"]
]
```

### 籃球迷
```json
[
  ["NBA 湖人", "NBA Lakers LeBron"],
  ["NBA 勇士", "NBA Warriors Curry"],
  ["NBA 塞爾提克", "NBA Celtics"],
  ["NBA 交易", "NBA trade deadline"],
  ["籃球總冠軍", "NBA Finals"]
]
```

### 只用 BBC（完全免費方案）
```json
{
  "sources": ["bbc"],
  "topics": [
    ["國際", "world"],
    ["英國", "uk"],
    ["科技", "technology"],
    ["經濟", "business"]
  ]
}
```
