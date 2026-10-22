import requests, feedparser, json
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

def clean_text(s): return BeautifulSoup(s or "", "html.parser").get_text(" ", strip=True)

# 👇 新增：精准提取原文的发布时间
def get_real_date(entry):
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) + timedelta(hours=8)
            return dt.strftime("%Y-%m-%d")
        except: pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

FEEDS = [
    # --- 原有核心源 ---
    {"url": "https://www.arabnews.com/rss.xml", "lang": "en"},
    {"url": "https://www.spa.gov.sa/rss.php", "lang": "en"},
    {"url": "https://www.zawya.com/en/rss", "lang": "en"},
    {"url": "https://www.argaam.com/en/rss", "lang": "en"},
    {"url": "https://gulfnews.com/rss/saudi", "lang": "en"},
    {"url": "https://aawsat.com/english/rss", "lang": "en"},
    {"url": "https://saudigazette.com.sa/rss", "lang": "en"},
    {"url": "https://gulfnews.com/rss/uae", "lang": "en"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "lang": "en"},
    # --- 原有阿语源 ---
    {"url": "https://www.alriyadh.com/rss", "lang": "ar"},
    {"url": "https://www.okaz.com.sa/rss", "lang": "ar"},
    {"url": "https://www.zawya.com/ar/rss", "lang": "ar"},
    # --- 新增：商业与财经资讯 ---
    {"url": "https://www.agbi.com/feed/", "lang": "en"},
    {"url": "http://tradearabia.com/rss/news.xml", "lang": "en"},
    # --- 新增：创投与科技媒体 ---
    {"url": "https://www.menabytes.com/feed/", "lang": "en"},
    {"url": "https://www.fwdstart.me/feed", "lang": "en"},
    {"url": "https://startuphub.today/feed/", "lang": "en"},
    {"url": "https://techscoop.io/feed/", "lang": "en"},
    # --- 新增：华人社区 ---
    {"url": "http://www.dubaichina.com/feed", "lang": "zh"},
    # --- 新增：Google News 精准兜底 ---
    {"url": "https://news.google.com/rss/search?q=site:zatca.gov.sa+OR+%22Saudi+tax%22&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=site:stats.gov.sa+OR+%22Saudi+economy+data%22&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=Amazon+Saudi+OR+Noon+Saudi+ecommerce&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=SPARK+Saudi+Arabia+energy+city&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=Saudi+MODON+industrial+city+investment&hl=en-US&gl=US&ceid=US:en", "lang": "en"}
]

KEYWORDS = [
    "saudi", "riyadh", "jeddah", "dammam", "neom", "red sea", "syria", "damascus", 
    "uae", "dubai", "qatar", "doha", "egypt", "cairo", "iraq", "baghdad", "jordan", 
    "kuwait", "oman", "bahrain", "business", "invest", "economy", "trade", "project", 
    "construction", "energy", "contract", "policy", "market", "company", "factory", 
    "manufacturing", "joint venture", "supply chain", "spark", "modon", "industrial park", 
    "economic zone", "free zone", "land lease", "localization", "nitaqat", "saber", 
    "compliance", "regulation", "tariff", "tax", "e-commerce", "startup", "funding", 
    "fintech", "saas", "logistics"
]

news_list = []
for feed_info in FEEDS:
    url = feed_info["url"]
    lang = feed_info["lang"]
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        feed = feedparser.parse(resp.content)
        for e in feed.entries[:20]:
            title = clean_text(e.get("title", ""))
            link = e.get("link", "")
            if not title or len(title) < 5: continue
                
            title_lower = title.lower()
            if lang != "zh" and not any(k in title_lower for k in KEYWORDS):
                continue 
                
            news_list.append({
                "title": title,
                "summary": clean_text(e.get("summary", ""))[:600],
                "url": link,
                "date": get_real_date(e), # 👈 这里使用精准提取的原文日期
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
