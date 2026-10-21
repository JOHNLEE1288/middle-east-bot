import requests, feedparser, json
from datetime import datetime, timezone
from bs4 import BeautifulSoup

def clean_text(s): return BeautifulSoup(s or "", "html.parser").get_text(" ", strip=True)

# 👇 新增阿拉伯语源，并打上语言标记
FEEDS = [
    {"url": "https://www.arabnews.com/rss.xml", "lang": "en"},               # 沙特英文
    {"url": "https://www.spa.gov.sa/rss.php", "lang": "en"},                 # 沙特英文
    {"url": "https://www.zawya.com/en/rss", "lang": "en"},                   # 中东英文
    {"url": "https://www.argaam.com/en/rss", "lang": "en"},                  # 沙特英文
    {"url": "https://gulfnews.com/rss/saudi", "lang": "en"},                 # 沙特英文
    {"url": "https://aawsat.com/english/rss", "lang": "en"},                 # 中东英文
    {"url": "https://saudigazette.com.sa/rss", "lang": "en"},                # 沙特英文
    {"url": "https://gulfnews.com/rss/uae", "lang": "en"},                   # 阿联酋英文
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "lang": "en"},      # 泛中东英文
    
    # 👇 以下是阿拉伯语源
    {"url": "https://www.alriyadh.com/rss", "lang": "ar"},                   # 利雅得报 (沙特最大阿语)
    {"url": "https://www.okaz.com.sa/rss", "lang": "ar"},                    # 欧卡兹报 (沙特阿语)
    {"url": "https://www.zawya.com/ar/rss", "lang": "ar"}                    # 中东阿语财经
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
                
            news_list.append({
                "title": title,
                "summary": clean_text(e.get("summary", ""))[:600],
                "url": link,
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "lang": lang # 👈 记录语种，传给腾讯云
            })
    except Exception as ex:
        print(f"Error {url}: {ex}")

# 去重
seen = set()
final_news = []
for n in news_list:
    if n["url"] not in seen:
        seen.add(n["url"])
        final_news.append(n)

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(final_news, f, ensure_ascii=False, indent=2)
print(f"抓取成功：{len(final_news)} 条")
