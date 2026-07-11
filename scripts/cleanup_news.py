#!/usr/bin/env python3
"""
清理脚本 - 移除体育/无关内容 + 同事件多源合并
同一事件多篇报道合并为一条，来源合并为「媒体A/媒体B/媒体C」格式
仅科技 + 美洲时政两个板块
"""
import json
import re
from collections import Counter

REMOVE_TITLES_KEYWORDS = [
    'messi', 'box score', 'game in miami', 'colombia clash', 'colombia fans',
    'profile and biography', 'rate the player', 'copa america', 'welsh teens arrested',
    'camilo duran', 'celtic complete',
    # 明显越界（非科技/美洲时政）
    'bavi', 'egypt win', 'trending news', 'ryanair',
    'step up strikes on russia', 'monaco bomb',
]

REMOVE_TITLE_PATTERNS = [
    r'openai.*advertising.*cannes', r'trump.*trade war.*news guide',
    r'wpi conversation', r'psni officer', r'takaichi visits',
    r'legendary japanese game director', r'kailash pilgrims', r'kenji takano',
    r'immigration wins.*centenarian', r'nato chief.*trump.*doubts',
    r'nato allies.*arctic', r'catholic bishops.*migrants', r'patriot passport',
    r'white house park.*trees', r'paraguay coach', r'decaffeinated',
    r'soccer-mad bangladesh', r'princess kate', r'liverpool.*sefton park',
    r'mang ujang', r'australian man charged', r'putin says russia',
    r'russian attacks kill', r'ukraine hits two russian', r'iraq detains politicians',
    r"singapore.*opposition.*singh", r'iran war developments',
    r'colombia.*portugal', r'colombia.*home team', r'us, ira[nm].*ramp',
    r'indian shares.*open steady',
]

# 每日事件组：运营者按当日实际抓取结果更新，确保同一事件跨媒体报道合并为一条
EVENT_GROUPS = [
    # 科技
    ("苹果起诉OpenAI窃取商业机密", [['apple', 'openai']]),
    ("SK海力士美国上市首发", [['hynix']]),
    ("Meta AI图片隐私争议", [['meta', 'image']]),
    ("南亚科Nanya 2027年资本开支", [['nanya']]),
    ("美国放宽对阿联酋AI芯片出口管制", [['uae', 'export']]),
    # 美洲时政
    ("休斯顿ICE枪击墨裔男子事件", [['ice', 'houston'], ['ice', 'mexican']]),
    ("美伊同意继续谈判", [['iran', 'talks', 'trump']]),
    ("特朗普两党住房法案", [['trump', 'housing', 'bill']]),
]


def should_remove(title):
    title_lower = title.lower()
    for kw in REMOVE_TITLES_KEYWORDS:
        if kw in title_lower:
            return True
    for pattern in REMOVE_TITLE_PATTERNS:
        if re.search(pattern, title_lower):
            return True
    return False


def match_event(title_lower):
    """按事件组匹配（词边界+可选复数s，避免 'ai' 误中 'said' / 'ice' 误中 'price' / 'image' 漏 'images'）"""
    for event_name, keyword_groups in EVENT_GROUPS:
        for kw_group in keyword_groups:
            if all(re.search(r'\b' + re.escape(kw) + r's?\b', title_lower) for kw in kw_group):
                return event_name
    return None


def merge_sources(articles):
    filtered = []
    removed_count = 0
    for art in articles:
        if should_remove(art['title_en']):
            removed_count += 1
        else:
            filtered.append(art)
    print(f"  过滤移除: {removed_count} 条")

    event_groups = {}
    ungrouped = []
    for art in filtered:
        title_lower = art['title_en'].lower()
        event = match_event(title_lower)
        if event:
            if event not in event_groups:
                event_groups[event] = []
            event_groups[event].append(art)
        else:
            ungrouped.append(art)

    merged = []
    merge_count = 0
    for event_name, group in event_groups.items():
        if len(group) == 1:
            merged.append(group[0])
        else:
            group.sort(key=lambda x: len(x['title_en']), reverse=True)
            main = group[0].copy()
            sources = []
            for art in group:
                src = art['source']
                if src not in sources:
                    sources.append(src)
            main['source'] = '/'.join(sources)
            main['_merged_sources'] = sources
            main['_merged_count'] = len(group)
            merged.append(main)
            merge_count += 1
            print(f"  合并 [{event_name}]: {' + '.join(sources)}")

    merged.extend(ungrouped)
    print(f"  事件合并: {merge_count} 组合并，{len(ungrouped)} 条未分组保留")
    return merged


if __name__ == '__main__':
    with open('/workspace/news-hub/scripts/filtered_articles.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    articles = data['articles']
    print(f"清理前: {len(articles)} 条")
    merged = merge_sources(articles)
    print(f"清理合并后: {len(merged)} 条")
    section_counts = Counter(a['section'] for a in merged)
    print(f"\n板块分布:")
    for s, c in section_counts.most_common():
        print(f"  {s}: {c}")
    multi_source = [a for a in merged if a.get('_merged_count', 1) > 1]
    print(f"\n多源合并文章: {len(multi_source)} 条")
    output_path = '/workspace/news-hub/scripts/clean_articles.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({'total': len(merged), 'articles': merged}, f, ensure_ascii=False, indent=2)
    print(f"\n已保存到: {output_path}")
