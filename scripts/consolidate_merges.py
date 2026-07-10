#!/usr/bin/env python3
"""补充合并：在 cleanup_news.py 输出之上，落实真正的「同事件多源」合并。
源合并为「媒体A/媒体B」格式。同时剔除聚合页/体育等低质量条目。
"""
import json

SRC = "/workspace/news-hub/scripts/clean_articles.json"

with open(SRC, encoding="utf-8") as f:
    data = json.load(f)
arts = data["articles"]
by_id = {a["id"]: a for a in arts}

# 需删除的聚合页/体育条
REMOVE_IDS = {
    "f64819127c49",  # 彭博 OpenAI Trending News 聚合页
    "da5c0a3b64f1",  # 彭博 Trump Tariffs Trending News 聚合页
    "3747b0928c1d",  # NYT 墨西哥vs英格兰 足球
    "b000de4793b9",  # BBC 阿根廷v威尔士 体育
}

# 同事件合并组：list of (主id, [其他id...])
MERGE_GROUPS = [
    # A. ICE 休斯顿枪击案 + 墨西哥回应
    ("420226c1b716", ["4cf718f695c5", "6e65bfc7a9b1", "cdf70b19ac56",
                       "98d1b78f0b18", "dbe04680cab9", "fb0c52a2954d"]),
    # B. OpenAI 版权诉讼制裁
    ("7e93f28aeac8", ["15dd79b0fdbb"]),
    # C. 新墨西哥 Epstein 牧场调查受阻
    ("79c94ffea4d2", ["bb10aeea68d4"]),
    # D. 墨西哥通胀创5年新低
    ("8189e5f38917", ["7c765a497da9"]),
    # E. 白宫建筑工程
    ("271600bd8f76", ["664e0158b0c3"]),
]

# 标记删除集合
merged_other_ids = set()
for _, others in MERGE_GROUPS:
    merged_other_ids.update(others)

removed = set(REMOVE_IDS) | merged_other_ids

# 构建合并后的主条目
merged_main_ids = {}
for main_id, others in MERGE_GROUPS:
    main = by_id[main_id].copy()
    sources = []
    for aid in [main_id] + others:
        src = by_id[aid]["source"]
        if src not in sources:
            sources.append(src)
    main["source"] = "/".join(sources)
    main["_merged_sources"] = sources
    main["_merged_count"] = len([main_id] + others)
    merged_main_ids[main_id] = main

# 重新组装最终列表
final = []
for a in arts:
    aid = a["id"]
    if aid in removed:
        continue
    if aid in merged_main_ids:
        final.append(merged_main_ids[aid])
    else:
        final.append(a)

# 统计
from collections import Counter
print(f"合并前(脚本输出): {len(arts)} 条")
print(f"剔除低质量: {len(REMOVE_IDS)} 条")
print(f"同事件合并组: {len(MERGE_GROUPS)} 组, 吸收 {len(merged_other_ids)} 条")
print(f"合并后: {len(final)} 条")
sec = Counter(a["section"] for a in final)
print("板块:", dict(sec))
multi = [a for a in final if a.get("_merged_count", 1) > 1]
print(f"多源合并文章: {len(multi)} 条")
for m in multi:
    print(f"  [{m['section']}] {m['source']} (x{m['_merged_count']})")

data["total"] = len(final)
data["articles"] = final
with open(SRC, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\n已写回: {SRC}")
