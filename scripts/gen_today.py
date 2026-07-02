#!/usr/bin/env python3
"""生成6月30日最终数据 - 复用已有翻译 + 补新文章"""
import json, re, os
from datetime import datetime, timezone, timedelta

with open('/workspace/news-hub/scripts/clean_articles.json','r') as f:
    data = json.load(f)
articles = data['articles']

# 移除体育/无关
remove_patterns = [r'colombia.*portugal', r'colombia.*home team', r'us, ira[nm].*ramp', r'indian shares.*open steady']
clean = [a for a in articles if not any(re.search(p, a['title_en'].lower()) for p in remove_patterns)]

# 加载已有翻译
with open('/workspace/news-hub/scripts/translations.json','r',encoding='utf-8') as f:
    old_trans = json.load(f)

def normalize(text):
    for o,n in {'\u2018':"'",'\u2019':"'",'\u201c':'"','\u201d':'"','\u2013':'-','\u2014':'-'}.items():
        text=text.replace(o,n)
    return text

# 所有翻译合并
ALL = {}
for k,v in old_trans.items():
    ALL[k] = (v['title'], v['summary'])

# 新增翻译（今天新出现的）
NEW = {
    "China's commerce ministry": ("中国商务部将20家日本实体列入出口管制清单","路透社报道，中国商务部宣布将20家日本实体列入出口管制清单，限制向这些实体出口特定物项。此举被视为中国在中日半导体争端中的最新反制措施。此前日本跟随美国对华芯片出口管制，限制先进半导体设备对华出口。中方此举可能影响日本半导体材料企业在华业务，也可能导致中日经贸关系进一步紧张。分析人士指出，出口管制正成为大国科技竞争的常态化工具，中日之间的技术博弈将长期持续。"),
    "China, India See Top Firms": ("中国和印度顶尖企业因AI滞后市值缩水","彭博社报道，中国和印度顶尖企业在AI竞赛中落后，导致市值占比下降。中国科技巨头受监管整顿和地缘政治影响，AI投入不及美国同行。印度企业则面临基础设施和人才瓶颈。相比之下，美国AI相关企业市值持续攀升，集中度加剧。报道指出，AI能力差距可能重塑全球科技产业格局，中美印三国的科技企业估值分化趋势短期内难以逆转。这也反映了AI产业链价值向美国集中的结构性趋势。"),
    "Apple hikes prices as memory": ("苹果因内存芯片成本飙升再次涨价","路透社报道，苹果因内存芯片成本大幅上涨再次上调产品价格。DRAM和NAND闪存价格受AI需求推动持续攀升，苹果作为消费电子巨头首当其冲。此次涨价涵盖Mac和iPad产品线，iPhone暂未调整但市场预期未来也将跟进。芯片成本上涨已成为整个消费电子行业面临的系统性压力。分析人士指出，苹果的涨价策略是在利润率和市场份额之间的艰难平衡，新兴市场消费者对价格更为敏感。"),
    "Apple seeks approval": ("金融时报：苹果寻求批准从黑名单中国公司采购芯片","路透社引述金融时报报道，苹果公司正在寻求美国政府批准，允许其从被列入黑名单的中国芯片公司采购部分组件。此举引发对中美科技脱钩边界的热议。苹果供应链深度依赖中国，完全脱钩成本巨大。苹果希望为非敏感用途的中国芯片获取豁免。分析人士指出，这一请求考验美国出口管制政策的弹性——过于宽松则削弱管制效力，过于严格则损害美国企业利益。"),
    "US-Iran Agree to Stop": ("美国和伊朗同意停止相互攻击","彭博社报道，美国和伊朗已达成协议同意停止相互攻击。这一协议在近期双方军事对抗升级后达成，旨在缓解中东紧张局势。协议细节尚未完全公开，预计涉及约束军事行动和建立沟通机制。分析人士指出，该协议是脆弱的临时安排，双方深层分歧未解。消息缓解了全球市场对中东冲突扩大的担忧，油价应声回落。但协议的持久性取决于双方的政治意愿和执行能力。"),
}
for k,v in NEW.items():
    ALL[k] = v

# 匹配翻译
SECTION_NAMES = {'tech':'科技产业','americas':'美洲时政','asia_pacific':'亚太时政'}
sections = {'tech':[], 'americas':[], 'asia_pacific':[]}
translated = 0
missing = []

for a in clean:
    t = normalize(a['title_en'])
    found = False
    for prefix, (title_zh, summary_zh) in ALL.items():
        p = normalize(prefix).lower()
        t_low = t.lower()
        if t_low.startswith(p) or p in t_low:
            a['title_zh'] = title_zh
            a['summary_zh'] = summary_zh
            sections[a['section']].append(a)
            translated += 1
            found = True
            break
    if not found:
        missing.append(a['title_en'])

print(f'翻译完成: {translated}条, 未匹配: {len(missing)}')
for m in missing:
    print(f'  缺: {m[:80]}')

# 生成JSON
beijing_tz = timezone(timedelta(hours=8))
now = datetime.now(beijing_tz)
daily = {'date':now.strftime('%Y-%m-%d'),'updated_at':now.strftime('%Y-%m-%d %H:%M 北京时间'),'total':translated,'sections':{}}
for sk,sn in SECTION_NAMES.items():
    sa = sections[sk]
    daily['sections'][sk] = {'name':sn,'count':len(sa),'articles':[{'id':a['id'],'title_zh':a['title_zh'],'summary_zh':a['summary_zh'],'title_en':a['title_en'],'source':a['source'],'url':a['url'],'published':a.get('published_display','')} for a in sa]}

path = f'/workspace/news-hub/data/{now.strftime("%Y-%m-%d")}.json'
with open(path,'w',encoding='utf-8') as f:
    json.dump(daily,f,ensure_ascii=False,indent=2)

# 更新index.json
with open('/workspace/news-hub/data/index.json','r',encoding='utf-8') as f:
    dates = json.load(f)
today = now.strftime('%Y-%m-%d')
if today not in dates:
    dates.insert(0, today)
with open('/workspace/news-hub/data/index.json','w',encoding='utf-8') as f:
    json.dump(dates,f,ensure_ascii=False,indent=2)

print(f'\n已保存: {path}')
for sk,sv in daily['sections'].items():
    print(f'  {sv["name"]}: {sv["count"]}条')
print(f'历史归档: {dates}')
multi = sum(1 for a in clean if a.get('_merged_count',1)>1)
print(f'多源合并: {multi}条')
