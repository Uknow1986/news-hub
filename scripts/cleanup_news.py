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

EVENT_GROUPS = [
    # 科技
    ("OpenAI/Anthropic限制AI模型", [['openai', 'anthropic', 'limit'], ['openai', 'limits', 'release'], ['openai', 'limits', 'access'], ['openai', 'defer', 'gpt'], ['anthropic', 'mythos'], ['anthropic', 'deal', 'lift'], ['anthropic', 'cleared'], ['anthropic', 'moves toward']]),
    ("Google限制Meta使用Gemini", [['google', 'limits', 'meta'], ['google caps meta'], ['google', 'meta', 'gemini']]),
    ("苹果涨价", [['apple', 'raising prices'], ['apple', 'price increases'], ['soaring ipad'], ['apple', 'micron', 'rough summer'], ['week in numbers', 'micron']]),
    ("芯片商借AI获利", [['chip makers', 'profiting'], ['chip makers', 'ai']]),
    ("中国网络安全AI追平Anthropic", [['china', 'matched anthropic'], ['china', 'cybersecurity', 'ai race']]),
    ("PC/主机涨价", [['tech firms', 'raising pc'], ['pc and console prices']]),
    ("OpenAI印度业务", [['openai hires uber'], ['openai.*india operations']]),
    ("Firmus与英伟达合作", [['firmus', 'nvidia'], ['firmus', 'ai access']]),
    ("OpenAI IPO", [['morgan stanley', 'goldman', 'openai'], ['openai', 'ipo', '2027']]),
    ("政府限制ChatGPT", [['tracking trump', 'chatgpt'], ['feds controlling chatgpt'], ['government', 'restrict', 'chatgpt']]),
    ("OpenAI内部争论", [['openai', 'mass shootings'], ['debate at openai']]),
    ("苹果Vision Pro人才流失", [['apple', 'vision pro', 'meade'], ['meade', 'openai']]),
    ("AI成本考验科技股", [['bloomberg intelligence', 'ai cost'], ['ai cost', 'tech stocks']]),
    # 美洲时政
    ("阿根廷内阁辞职", [['argentina cabinet chief'], ["milei.*cabinet chief"]]),
    ("美墨绝育蝇工厂", [['sterile fly', 'screwworm'], ['screwworm', 'cattle']]),
    ("特朗普关税欧洲", [['trump', 'tariff', 'europe'], ['trump', 'tariff', 'digital services'], ['trump', '100% tariff']]),
    ("Julia Letlow初选", [['letlow']]),
    ("委内瑞拉地震政治", [['venezuela', 'earthquakes'], ['machado', 'venezuela'], ['venezuela', 'quakes']]),
    ("墨西哥官员线人", [['mexican officials', 'informants']]),
    ("美墨加协定", [['us-mexico-canada'], ['usmca']]),
    ("Pemex新CFO", [['mexico', 'pemex'], ['pemex', 'cfo']]),
    ("DEA芬太尼调查", [['new mexico', 'dea'], ['dea', 'fentanyl']]),
    ("墨西哥央行会议", [['mexico cenbank'], ['mexico', 'finance ministry', 'trump']]),
    ("五角大楼任命", [['trump pentagon', 'appointee'], ['pentagon', 'republicans']]),
    ("特朗普伊朗制裁", [['trump', 'iran sanctions'], ['trump', 'iran', 'u-turn']]),
    ("巴西经常账户", [['brazil', 'current account']]),
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
    for event_name, keyword_groups in EVENT_GROUPS:
        for kw_group in keyword_groups:
            if all(kw in title_lower for kw in kw_group):
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
