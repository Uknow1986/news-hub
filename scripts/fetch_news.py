#!/usr/bin/env python3
"""
RSS 抓取脚本 - 从 8 家国际 TOP 媒体获取最近 24-48h 新闻
通过 Google News RSS 代理统一抓取，稳定可靠
"""
import feedparser
import json
import re
import time
import hashlib
import urllib.request
import ssl
from datetime import datetime, timedelta, timezone

# SSL 上下文（沙箱环境兼容）
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'

# 8 家媒体域名
MEDIA_SITES = {
    "Reuters": "reuters.com",
    "AP": "apnews.com",
    "BBC": "bbc.com",
    "Bloomberg": "bloomberg.com",
    "NYT": "nytimes.com",
    "WSJ": "wsj.com",
    "WaPo": "washingtonpost.com",
    "Nikkei": "asia.nikkei.com",
}

# 媒体中文名
MEDIA_CN = {
    "Reuters": "路透社",
    "AP": "美联社",
    "BBC": "BBC",
    "Bloomberg": "彭博社",
    "NYT": "纽约时报",
    "WSJ": "华尔街日报",
    "WaPo": "华盛顿邮报",
    "Nikkei": "日经亚洲",
}

# 主题搜索词（英文）- 仅科技 + 美洲时政
TOPIC_QUERIES = {
    "tech": [
        "AI OR artificial intelligence OR ChatGPT OR OpenAI OR LLM OR AGI",
        "semiconductor OR chip OR TSMC OR Nvidia OR Intel OR Samsung OR advanced materials",
        "smartphone OR iPhone OR Galaxy OR consumer electronics",
        "ICT OR telecom OR 5G OR Huawei OR ZTE OR cloud computing",
    ],
    "americas": [
        "Brazil OR Mexico OR Colombia OR Argentina OR Latin America",
        "US OR United States OR Washington OR Trump OR Biden",
    ],
}


def build_google_news_url(site, query, days=1):
    """构造 Google News RSS 搜索 URL"""
    q = f"site:{site} ({query}) when:{days}d"
    return f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=en-US&gl=US&ceid=US:en"


def parse_date(entry):
    """解析文章发布时间"""
    for attr in ['published_parsed', 'updated_parsed']:
        if hasattr(entry, attr) and getattr(entry, attr):
            t = getattr(entry, attr)
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except:
                pass
    return None


def is_within_24h(dt):
    """严格24小时内"""
    if dt is None:
        return True
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    return dt >= cutoff


def generate_id(title, url):
    raw = f"{title}|{url}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def clean_html(text):
    if '<' in text:
        text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


def detect_topic(title, summary):
    """根据标题和摘要检测文章属于哪个板块"""
    text = (title + ' ' + summary).lower()

    tech_keywords = ['ai', 'artificial intelligence', 'chip', 'semiconductor', 'gpu',
                     'tsmc', 'nvidia', 'intel', 'samsung', 'apple', 'iphone', 'android',
                     'smartphone', 'google', 'microsoft', 'openai', 'chatgpt', 'meta ',
                     'tech', 'software', 'cloud', '5g', 'telecom', 'robot', 'cyber',
                     'algorithm', 'llm', 'processor', 'qualcomm', 'amd', 'asml', 'huawei',
                     'digital', 'platform', 'app ', 'online', 'data center', 'encryption']
    americas_keywords = ['brazil', 'mexican', 'mexico', 'colombia', 'argentina',
                         'latin america', 'latam', 'peru', 'chile', 'venezuela',
                         'us ', 'u.s.', 'united states', 'washington', 'white house',
                         'trump', 'biden', 'congress', 'pentagon', 'state department']
    asia_keywords = ['china', 'chinese', 'beijing', 'shanghai', 'xi jinping',
                     'japan', 'japanese', 'tokyo', 'korea', 'korean', 'seoul',
                     'malaysia', 'indonesia', 'thailand', 'thai', 'philippines',
                     'philippine', 'asean', 'vietnam', 'singapore', 'taiwan',
                     'india', 'indian', 'modi', 'asia pacific', 'indo-pacific']

    is_tech = any(kw in text for kw in tech_keywords)
    is_americas = any(kw in text for kw in americas_keywords)
    is_asia = any(kw in text for kw in asia_keywords)

    return {
        'tech': is_tech,
        'americas': is_americas,
        'asia_pacific': is_asia,
    }


def fetch_feed(url):
    """用 urllib + feedparser 抓取 RSS"""
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    resp = urllib.request.urlopen(req, timeout=20, context=SSL_CTX)
    data = resp.read()
    return feedparser.parse(data)


def fetch_all_feeds():
    """抓取所有媒体的 RSS"""
    all_articles = []
    feed_status = {}

    for media_name, site_domain in MEDIA_SITES.items():
        for topic, queries in TOPIC_QUERIES.items():
            for query in queries:
                feed_name = f"{media_name}-{topic}"
                url = build_google_news_url(site_domain, query)
                print(f"  抓取: {feed_name} ...", end=" ", flush=True)
                try:
                    feed = fetch_feed(url)
                    count = 0
                    for entry in feed.entries:
                        title = entry.get('title', '').strip()
                        link = entry.get('link', '').strip()
                        summary = clean_html(entry.get('summary', ''))

                        if not title or not link:
                            continue

                        pub_date = parse_date(entry)
                        if pub_date and not is_within_24h(pub_date):
                            continue

                        # Google News 标题格式通常是 "标题 - 媒体名"，需要清理
                        title = re.sub(r'\s*-\s*(Reuters|AP News|BBC|Bloomberg|NYTimes\.com|Wall Street Journal|Washington Post|Nikkei Asia)\s*$', '', title)

                        topics = detect_topic(title, summary)

                        article = {
                            'id': generate_id(title, link),
                            'title_en': title,
                            'summary_en': summary[:500],
                            'url': link,
                            'source': MEDIA_CN[media_name],
                            'source_en': media_name,
                            'feed': feed_name,
                            'topic_tags': topics,
                            'published': pub_date.isoformat() if pub_date else '',
                            'published_display': pub_date.strftime('%Y-%m-%d %H:%M UTC') if pub_date else '',
                        }
                        all_articles.append(article)
                        count += 1

                    feed_status[feed_name] = count
                    print(f"✓ {count}")
                except Exception as e:
                    feed_status[feed_name] = -1
                    print(f"✗ {e}")
                time.sleep(0.3)

    return all_articles, feed_status


def deduplicate(articles):
    """去重"""
    seen_ids = set()
    seen_titles = set()
    unique = []

    for art in articles:
        if art['id'] in seen_ids:
            continue
        title_key = art['title_en'][:80].lower()
        if title_key in seen_titles:
            continue
        seen_ids.add(art['id'])
        seen_titles.add(title_key)
        unique.append(art)

    return unique


if __name__ == '__main__':
    import urllib.parse

    print("=" * 60)
    print("开始抓取 RSS 新闻源（Google News 代理）")
    print("=" * 60)

    articles, status = fetch_all_feeds()
    print(f"\n抓取完成，共 {len(articles)} 条（去重前）")

    articles = deduplicate(articles)
    print(f"去重后: {len(articles)} 条")

    # 统计各板块
    tech_count = sum(1 for a in articles if a['topic_tags']['tech'])
    americas_count = sum(1 for a in articles if a['topic_tags']['americas'])
    asia_count = sum(1 for a in articles if a['topic_tags']['asia_pacific'])
    print(f"\n板块分布（有交叉）:")
    print(f"  科技: {tech_count}")
    print(f"  美洲时政: {americas_count}")
    print(f"  亚太时政: {asia_count}")

    output_path = "/workspace/news-hub/scripts/raw_articles.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'fetched_at': datetime.now(timezone.utc).isoformat(),
            'total': len(articles),
            'feed_status': status,
            'articles': articles,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n原始数据已保存到: {output_path}")
