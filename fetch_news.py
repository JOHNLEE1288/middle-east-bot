import requests, feedparser, json
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

def clean_text(s): return BeautifulSoup(s or "", "html.parser").get_text(" ", strip=True)

def get_real_date(entry):
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) + timedelta(hours=8)
            return dt.strftime("%Y-%m-%d")
        except: pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

# 👇 大量使用 Google News 的 site: 语法，直捣黄龙抓取商业版块
FEEDS = [
    # 顶级媒体商业专栏
    {"url": "https://news.google.com/rss/search?q=site:arabnews.com+Business+OR+Economy&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=site:zawya.com+investment+OR+project&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=site:argaam.com+English+investment&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=site:gulfnews.com+Business+Saudi+OR+UAE&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    # 创投与科技媒体
    {"url": "https://www.menabytes.com/feed/", "lang": "en"},
    {"url": "https://www.fwdstart.me/feed", "lang": "en"},
    # 官方与园区（搜新闻代替直抓）
    {"url": "https://news.google.com/rss/search?q=SPARK+Saudi+Arabia+OR+MODON+OR+%22industrial+city%22+Saudi&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=Saudi+investment+OR+tender+OR+%22joint+venture%22+OR+factory&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=Syria+reconstruction+OR+investment+OR+business&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    # 阿语核心源
    {"url": "https://www.alriyadh.com/rss", "lang": "ar"},
    {"url": "https://www.okaz.com.sa/rss", "lang": "ar"}
]

news_list = []
for feed_info in FEEDS:
    url = feed_info["url"]
    lang = feed_info["lang"]
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        feed = feedparser.parse(resp.content)
        for e in feed.entries[:25]:
            title = clean_text(e.get("title", ""))
            link = e.get("link", "")
            if not title or len(title) < 5: continue
                
            news_list.append({
                "title": title,
                "summary": clean_text(e.get("summary", ""))[:600],
                "url": link,
                "date": get_real_date(e),
                "lang": lang 
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
