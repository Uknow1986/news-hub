#!/usr/bin/env python3
"""
翻译脚本 - 读取翻译数据，生成最终每日 JSON
"""
import json
from datetime import datetime, timezone, timedelta

SECTION_NAMES = {
    'tech': '科技产业',
    'americas': '美洲时政',
    'asia_pacific': '亚太时政',
}

def normalize_text(text):
    replacements = {
        '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def find_translation(title_en, translations):
    title_norm = normalize_text(title_en)
    for prefix, trans in translations.items():
        prefix_norm = normalize_text(prefix)
        if title_norm.startswith(prefix_norm):
            return trans['title'], trans['summary']
    return None, None

def main():
    with open('/workspace/news-hub/scripts/clean_articles.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open('/workspace/news-hub/scripts/translations.json', 'r', encoding='utf-8') as f:
        translations = json.load(f)

    articles = data['articles']
    print(f"待翻译: {len(articles)} 条")

    sections = {'tech': [], 'americas': [], 'asia_pacific': []}
    translated_count = 0
    missing = []

    for art in articles:
        title_zh, summary_zh = find_translation(art['title_en'], translations)
        if title_zh:
            art['title_zh'] = title_zh
            art['summary_zh'] = summary_zh
            translated_count += 1
            sections[art['section']].append(art)
        else:
            missing.append(art['title_en'])

    print(f"翻译完成: {translated_count}/{len(articles)}")
    if missing:
        print(f"未匹配: {len(missing)} 条")
        for t in missing:
            print(f"  ✗ {t[:80]}")

    beijing_tz = timezone(timedelta(hours=8))
    now_beijing = datetime.now(beijing_tz)

    daily_data = {
        'date': now_beijing.strftime('%Y-%m-%d'),
        'updated_at': now_beijing.strftime('%Y-%m-%d %H:%M 北京时间'),
        'total': translated_count,
        'sections': {},
    }

    for section_key, section_name in SECTION_NAMES.items():
        section_articles = sections[section_key]
        daily_data['sections'][section_key] = {
            'name': section_name,
            'count': len(section_articles),
            'articles': [],
        }
        for art in section_articles:
            daily_data['sections'][section_key]['articles'].append({
                'id': art['id'],
                'title_zh': art['title_zh'],
                'summary_zh': art['summary_zh'],
                'title_en': art['title_en'],
                'source': art['source'],
                'url': art['url'],
                'published': art.get('published_display', ''),
            })

    output_path = f'/workspace/news-hub/data/{now_beijing.strftime("%Y-%m-%d")}.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(daily_data, f, ensure_ascii=False, indent=2)

    print(f"\n最终数据已保存到: {output_path}")
    print(f"板块统计:")
    for sk, sv in daily_data['sections'].items():
        print(f"  {sv['name']}: {sv['count']} 条")

if __name__ == '__main__':
    main()
