import requests, feedparser, json, re
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

FEEDS = [
    # --- 英文核心商业源 ---
    {"url": "https://www.arabnews.com/rss.xml", "lang": "en"},
    {"url": "https://www.zawya.com/en/rss", "lang": "en"},
    {"url": "https://www.argaam.com/en/rss", "lang": "en"},
    {"url": "https://www.agbi.com/feed/", "lang": "en"},
    {"url": "http://tradearabia.com/rss/news.xml", "lang": "en"},
    {"url": "https://www.menabytes.com/feed/", "lang": "en"},
    {"url": "https://www.fwdstart.me/feed", "lang": "en"},
    {"url": "https://enterprise.news/rss", "lang": "en"},
    {"url": "https://www.wamda.com/feed", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=Saudi+Arabia+OR+UAE+OR+Qatar+investment+OR+supply+chain+OR+logistics+-war+-missile&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=Middle+East+business+OR+finance+OR+startup+funding&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=site:zawya.com+projects+OR+tender+OR+contract&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    
    # --- 阿拉伯语精选源 ---
    {"url": "https://www.alriyadh.com/rss", "lang": "ar"}, 
    {"url": "https://www.okaz.com.sa/rss", "lang": "ar"}, 
    {"url": "https://www.alegt.com/rss", "lang": "ar"}, 
    {"url": "https://aawsat.com/feed", "lang": "ar"}, 
    {"url": "https://www.alarabiya.net/feed/rss/ar", "lang": "ar"}, 
    {"url": "https://www.skynewsarabia.com/rss", "lang": "ar"} 
]

# ==========================================
# 👇 在这里添加你想自定义关注的词！（支持英文词根）
# 比如你最近想关注"太阳能"和"工厂"，就写 "solar", "factor"
# ==========================================
CUSTOM_KEYWORDS = [
    "solar", "desalination", "ev", "electric vehicle", 
    "factory", "manufactur", "warehouse", "logistics"
]

# 👇 之前的超大商业词库（全量合并，一个没少）
BUSINESS_KEYWORDS = [
    # 基础核心
    "invest", "trad", "econom", "business", "project", "market", "financ", "supply", "logistic",
    "agreement", "deal", "partnership", "joint venture", "acquisit", "ipo", "expans", "launch", "facilit", "plant", "factor", "bank", "fund",
    # 政策与合规
    "polic", "regulat", "law", "legislat", "legal", "complian", "reform", "decree", "royal order", "licens", "permit", "fdi", "ownership", "misa", 
    "tax", "tariff", "vat", "custom", "duty", "incentiv", "subsid", "exempt", "levy", "visa", "iqama", "nitaqat", "labor law",
    # 中资出海
    "china", "chinese", "sino", "beijing", "belt and road", "bri", "mou", "memorandum", "merger",
    # 项目与基建
    "tender", "bid", "contract", "award", "epc", "ppp", "mega", "neom", "red sea", "qiddiya", "diriyah", "spark", "modon", "giga", 
    "infrastructur", "construct", "road", "highway", "bridge", "railway", "metro", "airport", "port", "hous", "real estate", "contractor", "build",
    # 市场与需求
    "demand", "consum", "import", "export", "shortag", "growth", "boom", "trend", "shift", "transform", "diversif", "vision 2030",
    "aramco", "sabic", "pif", "adnoc", "mubadala", "distributor", "agent", "supplier", "vendor", "sourcing",
    # 成本与风险
    "land", "lease", "industrial zone", "free zone", "sez", "utilit", "power", "water", "rent", "cost", "expens", "inflation", "wage", "overhead",
    "ship", "freight", "maritim", "rout", "suez", "risk", "volatil", "currenc", "fx", "exchange rate", "delay", "disrupt",
    # 活动与展会
    "delegat", "visit", "summit", "forum", "confer", "meet", "bilateral", "diplomat", "mission", "expo", "exhibit", "trade show", "gitex", "leap", "big 5", "cityscape",
    # 行业词
    "machin", "equipment", "excavator", "crane", "bulldozer", "spare part", 
    "energ", "oil", "gas", "renew", "wind", "hydrogen", "nuclear", "power plant", "electric", "grid", 
    "production", "assembly", "industry",
    "mining", "mineral", "gold", "copper", "phosphat", "iron", "ore", "quarry", "metal",
    "supply chain", "warehous", "storag", "distribution", "truck", "cold chain", 
    "tech", "technolog", "startup", "vc", "venture capital", "seed", "series a", "fintech", "ai", "artificial intelligence", "saas", "digital", "cloud", "cybersecur",
    "e-commerce", "online shopp", "marketplace", "retail", "platform", "amazon", "noon", "deliver", "fulfillment", "payment"
]

# 把所有词合并（商业词 + 你的自定义词）
ALL_BUSINESS_WORDS = BUSINESS_KEYWORDS + CUSTOM_KEYWORDS
bus_pattern = re.compile(r'(' + '|'.join(ALL_BUSINESS_WORDS) + r')', re.IGNORECASE)

# 战争词边界匹配
WAR_KEYWORDS = [
    r"\bmissile", r"\bairstrike", r"\bkilled", r"\bwar", r"\battack", r"\bmilitary", r"\btroop", r"\bidf", r"\bhouthi", r"\bbomb", r"\bweapon", r"\bterror", r"\bconflict",
    r"\bdrone", r"\bmilitant", r"\brebel", r"\bcasualt", r"\bceasefire", r"\bhostag", r"\barmy", r"\bnavy", r"\bair force", r"\bretaliat", r"\bstrike"
]
war_pattern = re.compile(r'(' + '|'.join(WAR_KEYWORDS) + r')', re.IGNORECASE)

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
            summary = clean_text(e.get("summary", ""))
            if not title or len(title) < 5: continue
            
            text_to_check = title + " " + summary
            
            # 1. 斩杀线：只要命中反战词，直接抛弃
            if war_pattern.search(text_to_check): continue
            
            # 2. 准入线：命中总词库才保留
            if not bus_pattern.search(text_to_check): continue
                
            news_list.append({
                "title": title,
                "summary": summary[:600],
                "url": link,
                "date": get_real_date(e),
                "lang": lang 
            })
    except Exception as ex: pass

seen = set()
final_news = []
for n in news_list:
    if n["url"] not in seen:
        seen.add(n["url"])
        final_news.append(n)

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(final_news, f, ensure_ascii=False, indent=2)
print(f"抓取成功：{len(final_news)} 条商业新闻")
