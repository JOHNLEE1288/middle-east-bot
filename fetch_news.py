import requests, feedparser, json
from datetime import datetime, timezone
from bs4 import BeautifulSoup

def clean_text(s): return BeautifulSoup(s or "", "html.parser").get_text(" ", strip=True)

FEEDS = [
    "https://www.arabnews.com/rss.xml",          # 沙特
    "https://www.spa.gov.sa/rss.php",            # 沙特
    "https://www.zawya.com/en/rss",              # 中东商业
    "https://www.argaam.com/en/rss",             # 沙特财经
    "https://gulfnews.com/rss/saudi",            # 沙特(海湾新闻)
    "https://aawsat.com/english/rss",            # 中东报
    "https://saudigazette.com.sa/rss",           # 沙特公报
    "https://gulfnews.com/rss/uae",              # 阿联酋(海湾新闻)
    "https://www.aljazeera.com/xml/rss/all.xml"  # 半岛电视台(泛中东)
]

# 增加中东国家和商业关键词，保留更多有用信息
KEYWORDS = [
    "saudi", "riyadh", "jeddah", "syria", "damascus", "uae", "dubai", "qatar", "doha",
    "egypt", "cairo", "iraq", "baghdad", "jordan", "amman", "kuwait", "oman", "bahrain",
    "business", "invest", "economy", "trade", "project", "construction", "energy", "contract"
]

news_list = []
for url in FEEDS:
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        feed = feedparser.parse(resp.content)
        for e in feed.entries[:25]:
            title = clean_text(e.get("title", ""))
            link = e.get("link", "")
            if not title or len(title) < 5: continue
            
            title_lower = title.lower()
            # 只要标题里有中东国家或商业词，就保留
            if not any(k in title_lower for k in KEYWORDS):
                continue 
                
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
print(f"抓取成功：{len(final_news)} 条")
