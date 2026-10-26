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

# ==========================================
# 👇 全网最强新闻源矩阵
# ==========================================
FEEDS = [
    # 官方与叙利亚特定源
    {"url": "https://sana.sy/en/?feed=rss2", "lang": "en"},
    {"url": "https://syriadirect.org/feed/", "lang": "en"},
    
    # 顶级英文商业大报
    {"url": "https://www.arabnews.com/rss.xml", "lang": "en"},
    {"url": "https://www.zawya.com/en/rss", "lang": "en"},
    {"url": "https://www.argaam.com/en/rss", "lang": "en"},
    {"url": "https://www.agbi.com/feed/", "lang": "en"},
    {"url": "https://enterprise.news/rss", "lang": "en"},
    {"url": "https://www.arabianbusiness.com/rss", "lang": "en"},
    {"url": "https://www.ameinfo.com/rss", "lang": "en"},
    {"url": "http://tradearabia.com/rss/news.xml", "lang": "en"},
    
    # 海湾地区顶级综合大报
    {"url": "https://gulfnews.com/rss", "lang": "en"},
    {"url": "https://www.khaleejtimes.com/rss", "lang": "en"},
    {"url": "https://www.thenationalnews.com/rss", "lang": "en"},
    {"url": "https://saudigazette.com.sa/rss", "lang": "en"},
    
    # 中国视角
    {"url": "https://www.chinadaily.com.cn/rss/mideast_rss.xml", "lang": "en"},
    
    # 创投、科技与垂直行业
    {"url": "https://www.wamda.com/feed", "lang": "en"},
    {"url": "https://www.menabytes.com/feed/", "lang": "en"},
    {"url": "https://www.fwdstart.me/feed", "lang": "en"},
    {"url": "https://www.constructionweekonline.com/rss", "lang": "en"},
    {"url": "https://www.utilities-me.com/rss", "lang": "en"},
    {"url": "https://coingeek.com/feed/", "lang": "en"},
    {"url": "https://www.logisticsmiddleeast.com/rss", "lang": "en"},
    
    # 阿拉伯语核心源
    {"url": "https://www.alriyadh.com/rss", "lang": "ar"},
    {"url": "https://www.okaz.com.sa/rss", "lang": "ar"},
    {"url": "https://www.alegt.com/rss", "lang": "ar"},
    {"url": "https://aawsat.com/feed", "lang": "ar"},
    {"url": "https://www.alarabiya.net/feed/rss/ar", "lang": "ar"},
    {"url": "https://www.skynewsarabia.com/rss", "lang": "ar"},
    {"url": "https://www.aljazeera.net/rss", "lang": "ar"},
    {"url": "https://arabic.cnn.com/rss", "lang": "ar"},
    
    # 谷歌精准兜底源 (突破无RSS的网站)
    {"url": "https://news.google.com/rss/search?q=Saudi+Arabia+OR+UAE+OR+Qatar+investment+OR+supply+chain+OR+logistics+-war+-missile&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=Middle+East+business+OR+finance+OR+startup+funding&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=site:zawya.com+projects+OR+tender+OR+contract&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=site:meed.com+project+OR+contract&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=site:spa.gov.sa+OR+site:wam.ae+OR+site:qna.org.qa+OR+site:kuna.net.kw&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=site:misa.gov.sa+OR+site:modon.gov.sa+OR+site:spark.sa+OR+site:investuae.com&hl=en-US&gl=US&ceid=US:en", "lang": "en"},
    {"url": "https://news.google.com/rss/search?q=Middle+East+investment+OR+business+site:reuters.com+OR+site:bloomberg.com+OR+site:cnbc.com&hl=en-US&gl=US&ceid=US:en", "lang": "en"}
]

# ==========================================
# 👇 终极全量词根库 (含中东专属政务、园区)
# ==========================================
BUSINESS_KEYWORDS = [
    # 【1. 中东超级项目与主权基金】
    "spark", "modon", "neom", "red sea", "qiddiya", "diriyah", "roshn", "mise", "giga", "riyadh air", "vision 2030", "saudi green initiative", "misa", "pif", "aramco", "sabic", "adnoc", "mubadala", "masdar", "nupco", "stc", "mobily", "zain", "salic", "maaden",
    # 【2. 中东政务、合规、税务与招投标平台专有词】
    "nitaqat", "qiwa", "zatca", "iktva", "saber", "sfda", "gosi", "etimad", "saudization", "emiratisation", "local content", "rhq", "mohre", "ded", "dmcc", "adgm", "difc", "jafza", "saif zone", "saudi custom", "uae custom", "rera", "sama", "cma", "sabb", "tadawul",
    # 【3. 投资政策、法律法规与合规】
    "polic", "regulat", "law", "legislat", "legal", "compli", "reform", "decree", "licens", "permit", "fdi", "owner", "tax", "tariff", "vat", "custom", "duty", "incentiv", "subsid", "exempt", "levy", "visa", "iqama", "labor law", "residency", "privatiz", "anti-dumping", "arbitrat", "intellectu", "copyright", "trademark", "data protect", "privacy", "antitrust", "bankrupt", "dispute",
    # 【4. 中国企业出海与投资并购动作】
    "china", "chinese", "sino", "beijing", "belt and road", "bri", "mou", "memorandum", "merg", "subsidi", "branch", "factor setup", "assembly line", "procurement", "bid", "sourc", "joint venture", "jv", "greenfield", "brownfield", "offtake", "equity", "acquir", "takeover", "partner", "consortium", "spv", "localiz", "tech transfer",
    # 【5. 基础商业、项目与基建】
    "invest", "trad", "econom", "business", "project", "market", "financ", "suppli", "logistic", "agre", "deal", "ipo", "expans", "launch", "facilit", "factor", "bank", "fund", "tender", "contract", "award", "epc", "ppp", "mega", "infrastructur", "construct", "road", "highway", "bridge", "railway", "metro", "airport", "port", "hous", "real estate", "contractor", "build", "civil engineer", "design", "consult", "architectur", "master plan", "urban plan", "smart city", "utilit", "power grid", "water grid", "transmi", "distribut", "substat",
    # 【6. 市场、产业需求与前沿科技】
    "demand", "consum", "import", "export", "shortag", "growth", "boom", "trend", "shift", "transform", "diversif", "distributor", "agent", "supplier", "vendor", "data center", "cloud comput", "metavers", "gam", "esport", "web3", "blockchai", "crypto", "fintech", "digital", "e-commerce", "marketplace", "retail", "platform", "amazon", "noon", "deliver", "fulfill", "payment", "warehous", "storag", "cold chain", "last mile", "ai", "artificial intelligence", "machine learn", "cybersecur", "saas", "paas", "iaas", "iot", "smart home", "edtech", "healthtech", "agritech", "proptech",
    # 【7. 企业落地条件与经营成本】
    "land", "lease", "industrial zone", "free zone", "sez", "rent", "cost", "expen", "inflat", "wage", "overhead", "labor cost", "energy cost", "tariff", "operat", "capit", "break-even", "roi", "feasibil",
    # 【8. 贸易环境与投资风险】
    "trade war", "sanction", "embargo", "barrier", "currenc", "fx", "exchang", "devalu", "interest rate", "cpi", "gdp", "sovereign", "credit rat", "default", "volatil", "geopolit", "political", "complian", "aml", "anti-money launder", "kyc", "fraud", "corrupt", "bribe",
    # 【9. 政企交流与展会活动】
    "delegat", "visit", "summit", "forum", "confer", "meet", "bilateral", "diplomat", "mission", "expo", "exhibit", "trade show", "gitex", "leap", "big 5", "cityscape", "adipiec", "gulfood", "intersec", "saudia build", "saudi expo", "cop28", "cop29",
    # 【10. 垂直行业】
    "machin", "equipment", "excavator", "crane", "bulldozer", "spare part", "heavi", "energ", "oil", "gas", "renew", "wind", "hydrogen", "nuclear", "power plant", "electr", "grid", "solar", "desalinat", "green hydrogen", "blue hydrogen", "wind farm", "pv", "concentrat", "battery", "storag", "bess", "ccus", "carbon captur", "carbon credit", "esg", "sustainabil", "product", "assembl", "industri", "manufactur", "pharmaceut", "medic", "healthcar", "hospital", "clinic", "min", "mineral", "gold", "copper", "phosphat", "iron", "ore", "quarry", "metal", "aluminum", "steel", "petrochem", "fertiliz", "cement", "glass", "ceramic", "automot", "ev", "electric vehicl", "auto part", "textil", "food process", "agricultur", "agri", "poultry", "livestoc", "aquacultur"
]

# 👇 高压反战/废话拦截
WAR_KEYWORDS = [
    r"\bmissile", r"\bairstrike", r"\bkilled", r"\bwar", r"\battack", r"\bmilitary", r"\btroop", r"\bidf", r"\bhouthi", r"\bbomb", r"\bweapon", r"\bterror", r"\bconflict",
    r"\bdrone", r"\bmilitant", r"\brebel", r"\bcasualt", r"\bceasefire", r"\bhostag", r"\barmy", r"\bnavy", r"\bair force", r"\bretaliat", r"\bstrike",
    r"\bsanction", r"\brefugee", r"\bgeopolitical tension", r"\binvasion", r"\bartillery", r"\bwarplane", r"\bfighter jet", r"\bwounded", r"\bdead", r"\bviolence", r"\bclash", r"\bunrest", r"\bprotest", r"\briot", r"\binsurgency", r"\bcoup", r"\bassassination", r"\bblockade", r"\bsiege"
]

bus_pattern = re.compile(r'(' + '|'.join(BUSINESS_KEYWORDS) + r')', re.IGNORECASE)
war_pattern = re.compile(r'(' + '|'.join(WAR_KEYWORDS) + r')', re.IGNORECASE)

news_list = []
for feed_info in FEEDS:
    url = feed_info["url"]
    lang = feed_info["lang"]
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        feed = feedparser.parse(resp.content)
        for e in feed.entries[:30]:
            title = clean_text(e.get("title", ""))
            link = e.get("link", "")
            summary = clean_text(e.get("summary", ""))
            if not title or len(title) < 5: continue
            
            text_to_check = title + " " + summary
            
            if war_pattern.search(text_to_check): continue
            if not bus_pattern.search(text_to_check): continue
                
            news_list.append({
                "title": title,
                "summary": summary[:600],
                "url": link,
                "date": get_real_date(e),
                "lang": lang 
            })
    except Exception as ex: 
        pass

seen = set()
final_news = []
for n in news_list:
    if n["url"] not in seen:
        seen.add(n["url"])
        final_news.append(n)

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(final_news, f, ensure_ascii=False, indent=2)
print(f"抓取成功：{len(final_news)} 条商业新闻")
