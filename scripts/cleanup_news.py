#!/usr/bin/env python3
"""
清理脚本 - 移除体育/无关内容 + 同事件多源合并 + 板块重分类
同一事件多篇报道合并为一条，来源合并为「媒体A/媒体B/媒体C」格式
仅科技 + 美洲时政两个板块

每日事件组与移除列表：由运营者按当日实际抓取结果更新（见 EVENT_GROUPS / REMOVE_*）。
"""
import json
import re
from collections import Counter

# ---------------------------------------------------------------------------
# 1) 移除列表：与「科技 + 美洲时政」无关的内容
#    体育赛事、ETF/股票行情页、乌克兰/俄罗斯、西班牙/欧洲、伊朗(非美行动)、
#    以巴/西岸、孟加拉/津巴布韦、赞比亚(非洲)、彭博/混合轮替稿 等
# ---------------------------------------------------------------------------
REMOVE_TITLES_KEYWORDS = [
    # 体育（足球/橄榄球/网球/高尔夫/棒球/赛车/帆船/奥运）
    'wimbledon', 'cricket', 'konsa', 'chelsea', 'bull run',
    'nations championship', 'box score', 'messi', 'mega-preview',
    'soccer', 'colombian soccer', 'quarter-final', 'mitchell out',
    'argentina win at home over wales',
    'nascar', 'yankees', 'nationals', 'world sailing', 'olympic',
    'lautaro', 'martinez', 'jim gracey', 'sports journalist',
    'evian', 'haeran ryu', 'brooke henderson', 'golf', 'zverev',
    'fifa', 'england win', 'argentina get ready', 'fans in london',
    'scaloni', 'switzerland', 'var rule', 'andy burnham', 'kumuu ahaa',
    # 股票/ETF 行情页（非新闻）
    'etf', 'plc', 'sdr', 'bdr', 'octave intelligence',
    'space exploration technologies corp',
    'global x asia semiconductor etf', 't-rex 2x long', 'corgi lrcx',
    # 非美洲地缘（乌克兰/俄罗斯/欧洲/英国/西班牙/澳洲/亚太）
    'ukraine', 'zelenskiy', 'zelensky', 'russian attacks',
    'wildfire', 'spain', 'gibraltar', 'australia', 'superannuation',
    'typhoon', 'bavi', 'china',
    # 以巴 / 西岸
    'west bank', 'israeli military', 'israeli settlers',
    # 亚洲/非洲（无关）
    'bangladesh', 'zimbabwe', 'zambia',
    # 外语重复稿（BBC 索马里语版，与英文稿重复）
    'ku dhawaaqay',
]

REMOVE_TITLE_PATTERNS = [
    # 伊朗(非美国行动)：仅移除伊朗单方面宣布/解读类，保留「美国打击伊朗」美方行动稿
    r'iran declares strait of hormuz',
    r'irgc navy says strait of hormuz',
    r'iran war: what is happening in the strait',
    # 彭博混合轮替稿（多主题拼凑，非单事件报道）
    r'trump remembers lindsey graham, us-iran',
    # 阿根廷足协邮件被黑（体育相关网络事件，非科技主线）
    r'argentina investigating cyberattack',
    # 彭博混合轮替稿（多主题拼凑，非单事件报道）
    r'iran rejects us talks.*apple sues openai',
    r"trump threatens to .?decimate.? iran, apple sues openai, more",
    # 其他已知越界内容
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

# ---------------------------------------------------------------------------
# 2) 每日事件组：将同一事件跨媒体报道合并为一条
#    关键词组用「词边界 + 可选复数 s」匹配，避免 'ai' 误中 'said' 等
# ---------------------------------------------------------------------------
EVENT_GROUPS = [
    # 美洲时政：林赛·格雷厄姆逝世（多源合并）
    ("美参议员林赛·格雷厄姆逝世", [
        ['lindsey', 'graham'],
        ['graham', 'dies'],
        ['graham', 'death'],
        ['graham', 'trump'],
        ['key', 'ally', 'trump', 'dies'],
    ]),
    # 美洲时政：美国对伊朗发动打击 / 霍尔木兹海峡对峙
    ("美国对伊朗发动打击 霍尔木兹海峡对峙升级", [
        ['iran', 'stri'],
        ['strait', 'hormuz'],
        ['us', 'iran'],
    ]),
    # 美洲时政：委内瑞拉强震
    ("委内瑞拉强震", [
        ['venezuela', 'quake'],
        ['venezuelan', 'quake'],
        ['venezuela', 'earthquake'],
        ['venezuelan', 'earthquake'],
    ]),
]

# ---------------------------------------------------------------------------
# 3) 板块重分类：清理后，按内容将每条归入 tech / americas
#    含强科技信号 -> tech；其余（美国/拉美政治） -> americas
# ---------------------------------------------------------------------------
TECH_PATTERNS = [
    r'\bai\b', r'artificial intelligence', r'chatgpt', r'openai', r'\bgpt\b',
    r'anthropic', r'claude', r'gemini', r'\bllm\b', r'machine learning',
    r'semiconductor', r'\bchip\b', r'tsmc', r'nvidia', r'intel', r'samsung',
    r'\bamd\b', r'asml', r'qualcomm', r'iphone', r'smartphone', r'galaxy',
    r'android', r'consumer electronics', r'\b5g\b', r'telecom', r'huawei',
    r'\bzte\b', r'data center', r'cloud computing', r'cybersecurity', r'\brobot\b',
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
    """按事件组匹配（词首边界匹配，兼容复数/-ed/派生词：strikes/striking、
    subpoenaed、Venezuelan、quakes 等）"""
    for event_name, keyword_groups in EVENT_GROUPS:
        for kw_group in keyword_groups:
            if all(re.search(r'(?<!\w)' + re.escape(kw), title_lower) for kw in kw_group):
                return event_name
    return None


def classify_section(title, summary):
    """重分类到 tech / americas"""
    text = (title + ' ' + summary).lower()
    for pat in TECH_PATTERNS:
        if re.search(pat, text):
            return 'tech'
    return 'americas'


def merge_sources(articles):
    filtered = []
    removed_count = 0
    for art in articles:
        if should_remove(art['title_en']):
            removed_count += 1
        else:
            filtered.append(art)
    print(f"  过滤移除: {removed_count} 条")

    # 事件合并（跨板块合并同一事件）
    event_groups = {}
    ungrouped = []
    for art in filtered:
        title_lower = art['title_en'].lower()
        event = match_event(title_lower)
        if event:
            event_groups.setdefault(event, []).append(art)
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

    # 重分类板块
    for art in merged:
        art['section'] = classify_section(art['title_en'], art.get('summary_en', ''))

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
