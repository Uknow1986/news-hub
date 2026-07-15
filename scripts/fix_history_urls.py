#!/usr/bin/env python3
"""
修复历史数据中的链接：
将 data/*.json 里的 Google News 编码中转链接(news.google.com/articles/...)
替换为「标题 + 来源域名」的 Google 搜索链接。

原因：Google News 编码链接有时效性且无法解码出真实原文 URL，过期即失效。
搜索链接长期有效，点击后可定位到该媒体的原文出处。
"""
import json, glob, urllib.parse

SRC_DOMAIN = {
    '路透社': 'reuters.com', '美联社': 'apnews.com', 'BBC': 'bbc.com',
    '彭博社': 'bloomberg.com', '纽约时报': 'nytimes.com', '华尔街日报': 'wsj.com',
    '华盛顿邮报': 'washingtonpost.com', '日经亚洲': 'asia.nikkei.com'
}

DATA_DIR = '/workspace/news-hub/data'


def domain_for(source):
    for k, v in SRC_DOMAIN.items():
        if k in (source or ''):
            return v
    return None


def make_search_url(art):
    title = (art.get('title_en') or art.get('title_zh') or '').strip()
    dom = domain_for(art.get('source'))
    q = (f'site:{dom} ' if dom else '') + title
    return 'https://www.google.com/search?' + urllib.parse.urlencode({'q': q})


def fix_file(path):
    d = json.load(open(path, encoding='utf-8'))
    if not isinstance(d, dict):
        return 0
    changed = 0
    for sk, sec in d.get('sections', {}).items():
        arts = sec['articles'] if isinstance(sec, dict) else sec
        for a in arts:
            u = a.get('url', '')
            if 'news.google.com' in u:
                a['url'] = make_search_url(a)
                a['link_type'] = 'search'
                changed += 1
            else:
                a['link_type'] = 'direct'
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    return changed


def main():
    total = 0
    for f in sorted(glob.glob(f'{DATA_DIR}/*.json')):
        if f.endswith('/index.json'):
            continue
        c = fix_file(f)
        total += c
        print(f'{f.split("/")[-1]}: 修复 {c} 条')
    print(f'\n合计修复: {total} 条 Google News 编码链接 -> 搜索链接')


if __name__ == '__main__':
    main()
