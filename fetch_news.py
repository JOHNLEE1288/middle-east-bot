import requests, feedparser, json
from datetime import datetime, timezone
from bs4 import BeautifulSoup

def clean_text(s): return BeautifulSoup(s or "", "html.parser").get_text(" ", strip=True)

FEEDS = [
    "https://www.arabnews.com/rss.xml",
    "https://www.spa.gov.sa/rss.php",
    "https://www.zawya.com/en/rss"
]

# 👇 必须包含这些词之一，否则不要！
KEYWORDS = ["saudi", "riyadh", "jeddah", "business", "invest", "economy", "trade", "project", "syria", "damascus", "construction"]

news_list = []
for url in FEEDS:
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        feed = feedparser.parse(resp.content)
        for e in feed.entries[:30]:
            title = clean_text(e.get("title", ""))
            link = e.get("link", "")
            if not title or len(title) < 5: continue
            
            # 强制关键词过滤
            title_lower = title.lower()
            if not any(k in title_lower for k in KEYWORDS):
                continue # 如果不包含沙特/商业关键词，直接丢弃
                
            news_list.append({
                "title": title,
                "summary": clean_text(e.get("summary", ""))[:600],
                "url": link,
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")
            })
    except Exception as ex:
        print(f"Error {url}: {ex}")

seen = set()
final_news = []
for n in news_list:
    if n["url"] not in seen:
        seen.add(n["url"])
        final_news.append(n)

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(final_news, f, ensure_ascii=False, indent=2)
print(f"过滤后抓取成功：{len(final_news)} 条")
