#!/usr/bin/env python3
"""
筛选脚本 - 从原始文章中按相关性和权威性选出 50-80 条强相关新闻
"""
import json
import re
from datetime import datetime, timedelta, timezone

# 媒体权威性权重
SOURCE_WEIGHT = {
    "路透社": 1.0,
    "美联社": 1.0,
    "BBC": 0.95,
    "彭博社": 0.95,
    "纽约时报": 0.9,
    "华尔街日报": 0.9,
    "华盛顿邮报": 0.85,
    "日经亚洲": 0.85,
}

# 强相关关键词（出现即加分）
STRONG_KEYWORDS = {
    "tech": {
        # AI
        'ai': 3, 'artificial intelligence': 3, 'chatgpt': 3, 'openai': 3, 'gpt': 3,
        'anthropic': 3, 'claude': 3, 'gemini': 3, 'llm': 3, 'machine learning': 2,
        'deepmind': 2, 'generative ai': 3,
        # 半导体
        'semiconductor': 3, 'chip': 2, 'tsmc': 3, 'nvidia': 3, 'intel': 2,
        'samsung': 2, 'amd': 2, 'asml': 3, 'qualcomm': 2, 'foundry': 2,
        'processor': 1, 'gpu': 2, 'moore': 1,
        # 终端
        'iphone': 2, 'smartphone': 2, 'apple': 2, 'galaxy': 1, 'android': 1,
        'consumer electronics': 2,
        # ICT
        '5g': 2, 'telecom': 2, 'huawei': 2, 'zte': 2, 'ericsson': 1,
        'nokia': 1, 'broadband': 1, 'data center': 2, 'cloud': 1,
        'cybersecurity': 2, 'cyber': 1, 'encryption': 1,
        # 科技公司
        'google': 1, 'microsoft': 1, 'meta ': 1, 'amazon': 1, 'bytedance': 2,
        'tiktok': 2, 'tesla': 1, 'robot': 1,
    },
    "americas": {
        # 美洲国家
        'brazil': 3, 'brazilian': 3, 'lula': 3,
        'mexico': 3, 'mexican': 3, 'amlo': 2, 'sheinbaum': 3,
        'colombia': 3, 'colombian': 3,
        'argentina': 3, 'argentine': 3, 'milei': 3,
        'latin america': 2, 'latam': 2, 'peru': 2, 'chile': 2,
        'venezuela': 2, 'maduro': 2, 'cuba': 1,
        # 美国
        'trump': 2, 'biden': 2, 'white house': 2, 'congress': 1,
        'senate': 1, 'pentagon': 2, 'state department': 2,
        'tariff': 2, 'sanction': 2, 'trade war': 2,
        'nato': 1, 'oas': 1,
    },
    "asia_pacific": {
        # 中国
        'china': 2, 'chinese': 2, 'beijing': 2, 'xi jinping': 3,
        'shanghai': 1, 'ccp': 2, 'pla': 2, 'xinjiang': 1, 'taiwan': 2,
        'cross-strait': 2, 'south china sea': 2,
        # 日本
        'japan': 2, 'japanese': 2, 'tokyo': 2, 'kishida': 2, 'ishiba': 2,
        # 韩国
        'south korea': 3, 'korean': 1, 'seoul': 2, 'yoon': 2,
        # 东南亚
        'malaysia': 3, 'indonesia': 3, 'thailand': 3, 'thai': 2,
        'philippines': 3, 'philippine': 2, 'marcos': 2,
        'vietnam': 2, 'singapore': 1, 'asean': 2,
        # 印度
        'india': 2, 'indian': 2, 'modi': 2, 'new delhi': 1,
        # 地缘
        'indo-pacific': 2, 'quad': 2, 'apec': 1,
    }
}

# 负面关键词（降低不相关文章的分数）- 精确匹配，避免误杀
NEGATIVE_KEYWORDS = [
    # 体育（完整短语匹配）
    'world cup', 'knockout stage', 'group stage', 'rate the player',
    'match draws', 'wins group', 'penalty shootout', 'match preview',
    'player ratings', 'match report', 'kickoff', 'extra time',
    # 娱乐生活
    'celebrity gossip', 'film festival', 'travel guide',
    'horoscope', 'lottery results', 'crossword puzzle',
    # 金融行情页（非新闻）
    'futures prices and news', 'stock price target',
    'analyst rating', 'options flow',
    # Google News 聚合页
    'latest news & updates', 'see more coverage',
]

# 标题太短的视为聚合页/话题页，过滤掉
MIN_TITLE_LENGTH = 25


def score_article(article, section):
    """计算文章在某个板块的相关性分数"""
    text = (article['title_en'] + ' ' + article['summary_en']).lower()
    score = 0

    # 强相关关键词匹配
    for kw, weight in STRONG_KEYWORDS.get(section, {}).items():
        if kw in text:
            score += weight

    # 负面关键词减分
    for neg_kw in NEGATIVE_KEYWORDS:
        if neg_kw in text:
            score -= 3

    # 媒体权威性加权
    source = article.get('source', '')
    source_weight = SOURCE_WEIGHT.get(source, 0.8)
    score *= source_weight

    # 时效性加权（越新越好）
    if article.get('published'):
        try:
            pub = datetime.fromisoformat(article['published'])
            hours_ago = (datetime.now(timezone.utc) - pub).total_seconds() / 3600
            if hours_ago < 12:
                score *= 1.2
            elif hours_ago < 24:
                score *= 1.1
            elif hours_ago < 36:
                score *= 1.0
            else:
                score *= 0.8
        except:
            pass

    return score


def assign_primary_section(article):
    """分配文章到主要板块（取得分最高的板块）"""
    scores = {}
    for section in ['tech', 'americas', 'asia_pacific']:
        scores[section] = score_article(article, section)
    
    best_section = max(scores, key=scores.get)
    best_score = scores[best_section]
    
    return best_section, best_score, scores


def is_low_quality(article):
    """过滤低质量文章（聚合页、行情页、体育等）"""
    title = article['title_en']
    title_lower = title.lower()
    summary = article['summary_en']
    text = title_lower + ' ' + summary.lower()

    # 标题太短（话题页/聚合页）
    if len(title) < MIN_TITLE_LENGTH:
        return True

    # 含负面关键词
    for neg_kw in NEGATIVE_KEYWORDS:
        if neg_kw in text:
            return True

    # Google News 聚合页特征：标题是 "XXX | Latest News" 格式
    if '|' in title and ('latest' in title_lower or 'news' in title_lower and len(title) < 40):
        return True

    return False


def is_similar(title1, title2):
    """判断两个标题是否讲同一件事（简单词重叠率）"""
    words1 = set(title1.lower().split())
    words2 = set(title2.lower().split())
    if not words1 or not words2:
        return False
    overlap = len(words1 & words2)
    min_len = min(len(words1), len(words2))
    return overlap / min_len >= 0.6 and min_len >= 4


def filter_articles(articles, target_total=70):
    """筛选文章，按板块分配名额"""
    # 先过滤低质量
    clean = [a for a in articles if not is_low_quality(a)]
    print(f"  低质量过滤: {len(articles)} -> {len(clean)} 条")

    # 为每篇文章计算各板块得分和主板块
    scored = []
    for art in clean:
        section, score, all_scores = assign_primary_section(art)
        if score > 0:
            art['_primary_section'] = section
            art['_score'] = score
            art['_all_scores'] = all_scores
            scored.append(art)

    # 按板块分组并排序（仅科技+美洲，取消亚太）
    sections = {'tech': [], 'americas': []}
    for art in scored:
        if art['_primary_section'] in sections:
            sections[art['_primary_section']].append(art)

    # 每个板块取 top N
    quotas = {'tech': 35, 'americas': 35}

    final = []
    for section, arts in sections.items():
        arts.sort(key=lambda x: x['_score'], reverse=True)
        quota = quotas[section]
        selected = []
        seen_titles = []
        for art in arts:
            if len(selected) >= quota:
                break
            # 相似度去重
            is_dup = False
            for seen_title in seen_titles:
                if is_similar(art['title_en'], seen_title):
                    is_dup = True
                    break
            if not is_dup:
                art['section'] = section
                selected.append(art)
                seen_titles.append(art['title_en'])
        print(f"  {section}: 候选 {len(arts)} 条, 选中 {len(selected)} 条")
        final.extend(selected)

    # 按时间排序
    final.sort(key=lambda x: x.get('published', ''), reverse=True)

    return final


if __name__ == '__main__':
    print("=" * 60)
    print("开始筛选文章")
    print("=" * 60)

    with open('/workspace/news-hub/scripts/raw_articles.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    articles = data['articles']
    print(f"原始文章: {len(articles)} 条")

    final = filter_articles(articles, target_total=70)
    print(f"\n筛选后: {len(final)} 条")

    # 统计来源
    from collections import Counter
    source_counts = Counter(a['source'] for a in final)
    print("\n来源分布:")
    for s, c in source_counts.most_common():
        print(f"  {s}: {c}")

    # 清理临时字段
    for art in final:
        art.pop('_primary_section', None)
        art.pop('_score', None)
        art.pop('_all_scores', None)

    # 保存
    output_path = '/workspace/news-hub/scripts/filtered_articles.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'filtered_at': datetime.now(timezone.utc).isoformat(),
            'total': len(final),
            'articles': final,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n筛选结果已保存到: {output_path}")

    # 打印预览
    print("\n" + "=" * 60)
    print("选中文章预览:")
    print("=" * 60)
    for i, art in enumerate(final):
        print(f"\n[{i+1}] [{art['section']}] [{art['source']}]")
        print(f"  标题: {art['title_en'][:100]}")
        print(f"  摘要: {art['summary_en'][:120]}...")
        print(f"  链接: {art['url'][:80]}")
