#!/usr/bin/env python3
"""生成6月29日最终数据"""
import json
from datetime import datetime, timezone, timedelta

# 加载昨日翻译（复用）
with open('/workspace/news-hub/scripts/translations.json','r',encoding='utf-8') as f:
    old_trans = json.load(f)

with open('/workspace/news-hub/scripts/clean_articles.json','r',encoding='utf-8') as f:
    data = json.load(f)
articles = data['articles']

SECTION_NAMES = {'tech':'科技产业','americas':'美洲时政','asia_pacific':'亚太时政'}

def normalize(text):
    for o,n in {'\u2018':"'",'\u2019':"'",'\u201c':'"','\u201d':'"','\u2013':'-','\u2014':'-'}.items():
        text = text.replace(o,n)
    return text

def find_old(title_en):
    t = normalize(title_en)
    for prefix, trans in old_trans.items():
        if t.startswith(normalize(prefix)):
            return trans['title'], trans['summary']
    return None, None

# 新文章翻译
NEW = {
"Ant International-Backed Fintech": ("蚂蚁国际支持的金融科技独角兽申请菲律宾史上最大IPO","华尔街日报报道，一家由蚂蚁国际支持的金融科技独角兽已向菲律宾监管机构提交IPO申请，预计融资规模将创菲律宾历史纪录。此举标志着东南亚金融科技市场进入新阶段，该地区数字支付和在线借贷需求快速增长。蚂蚁国际的参与显示中国金融科技企业在海外市场的持续布局。菲律宾资本市场近年来逐步开放，IPO活跃度提升，此次上市若成功将提振投资者对东南亚金融科技板块的信心，也可能吸引更多区域独角兽走向公开市场。"),
"Philippines Sees Slower Growth": ("彭博社：菲律宾预计马科斯任期后增长放缓、比索走弱","彭博社报道，菲律宾预计在马科斯总统任期结束后经济增长将放缓，比索汇率面临持续压力。分析指出，菲律宾经济面临基础设施投资不足、通胀高企和财政赤字扩大等结构性挑战。马科斯政府推动的基础设施建设和外资吸引政策短期内提振了增长，但长期可持续性存疑。比索贬值将推高进口成本，加剧通胀压力。菲律宾央行可能在货币政策上面临增长与通胀之间的艰难平衡，国际评级机构也在密切关注其财政轨迹。"),
"South Korean President to unveil massive AI": ("韩国总统将公布大规模AI和芯片投资计划","路透社报道，韩国总统即将公布一项大规模AI和半导体投资计划，旨在巩固韩国在全球芯片产业的领先地位。计划预计涉及政府与三星、SK海力士等巨头的联合投资，覆盖AI芯片研发、先进制程产能扩张和人才培养。此举是韩国应对中美芯片竞争的战略举措，也是其「AI强国」战略的核心组成部分。韩国是全球存储芯片最大生产国之一，政府希望通过政策支持维持技术优势。计划还包括对AI初创企业的扶持和AI算力基础设施建设，预计将创造数万个高技能就业岗位。"),
"Facing China, one Taiwan Coast Guard": ("面对中国压力，一名台湾海巡人员从信仰中汲取力量","路透社报道，面对中国在台湾周边海域日益增加的灰色地带行动，台湾海巡署一线人员承受着巨大压力。报道聚焦一名海巡官员，他在高强度执勤中通过宗教信仰获得心理支撑。台湾海巡署近年来频繁应对中国海警船进入限制水域的事件，人员疲劳和心理压力问题日益突出。该报道反映了台海紧张局势对一线人员的深层影响，也揭示了非军事执法力量在地缘对抗中的角色。分析人士指出，中国的灰色地带策略正持续消耗台湾的执法资源。"),
"Mexico cenbank, finance ministry": ("墨西哥央行和财政部将在特朗普重返白宫前召开紧急会议","路透社报道，墨西哥央行和财政部将于周三举行联合新闻发布会，在特朗普即将重返白宫之际安抚市场情绪。特朗普此前威胁对墨西哥加征关税并重新谈判贸易协定，引发墨西哥比索大幅波动。央行和财政部预计将公布经济稳定措施和汇率干预预案。墨西哥经济高度依赖对美出口，特朗普的贸易政策可能对其造成重大冲击。市场参与者密切关注会议内容，预计央行可能调整利率路径或推出流动性支持工具以稳定金融市场。"),
"Philippines leads the world in rush to solar": ("电价飙升推动菲律宾领跑全球太阳能发展","路透社报道，菲律宾正以全球最快速度推进太阳能装机，高涨的电价和丰富的日照资源是主要驱动力。菲律宾电力价格在东南亚地区位居前列，太阳能成为降低用电成本的关键途径。政府推出了系列激励政策，包括税收减免和并网审批简化，吸引了大量国内外投资。分析指出，菲律宾的太阳能发展模式对其他东南亚岛国具有借鉴意义，但电网基础设施滞后和土地获取困难仍是瓶颈。能源转型也在帮助菲律宾减少对进口化石燃料的依赖，改善能源安全。"),
"Prabowo Risks Prompt Global Banks": ("普拉博沃政策风险促使全球银行从印尼撤资","彭博社报道，印尼总统普拉博沃的政策不确定性正促使全球银行从印尼撤出资金。普拉博沃上任后推行的一系列政策，包括资源民族主义倾向和财政扩张计划，引发外资担忧。多家国际银行已削减对印尼的风险敞口，印尼盾汇率承压。印尼是东南亚最大经济体，外资流出可能影响其经济增长前景。分析人士指出，普拉博沃需要在兑现竞选承诺和维护投资者信心之间取得平衡。印尼央行已干预汇市稳定汇率，但市场情绪恢复需要政策清晰度的提升。"),
"Firmus Technologies strikes AI": ("澳大利亚Firmus Technologies与英伟达达成AI算力合作","路透社报道，澳大利亚AI初创公司Firmus Technologies已与英伟达达成AI算力访问协议，获得英伟达GPU集群的使用权限。这将使Firmus能够为亚太地区客户提供AI训练和推理服务，降低该区域企业获取AI算力的门槛。澳大利亚正努力在AI产业链中寻找自己的定位，Firmus与英伟达的合作被视为澳企在全球AI竞赛中的突破。协议还涉及技术转移和本地人才培养，Firmus计划在澳大利亚建设AI算力中心。分析人士指出，亚太地区AI算力需求快速增长，澳洲凭借能源成本优势有望成为区域算力枢纽。"),
"Baidu's AI chip unit Kunlunxin": ("百度AI芯片子公司昆仑芯拟赴港IPO，估值目标500亿美元","路透社引述The Information报道，百度旗下AI芯片子公司昆仑芯计划在香港进行IPO，目标估值约500亿美元。昆仑芯是百度为减少对英伟达依赖而布局的芯片业务，产品覆盖AI训练和推理芯片。此次IPO若成功，将成为中国AI芯片领域最大规模的公开上市之一。百度希望通过分拆上市为昆仑芯引入战略投资者，加速芯片研发和商业化进程。在中美科技竞争背景下，中国AI芯片自主化需求迫切，昆仑芯的上市计划受到市场高度关注。"),
"Trump Pentagon appointee who has divided": ("五角大楼特朗普任命者引发共和党高层内部分裂","华盛顿邮报报道，特朗普在五角大楼的一项关键任命在共和党高层中引发分裂。部分共和党议员支持该任命，认为其符合改革国防部的需要；另一派则担忧任命者的资质和政策方向可能损害军方专业性和战备能力。这一分歧反映了共和党内在国防政策上的深层矛盾——一派主张激进改革以应对中国威胁，另一派强调维护传统军事体制的稳定性。五角大楼的人事动荡可能影响美国国防政策的连续性和盟友信心。国会确认程序将成为两派较量的战场。"),
"Trump's U-Turn on Iran Sanctions": ("特朗普对伊制裁政策转向或将瓦解数十年遏制体系","彭博社报道，特朗普若在对伊制裁政策上转向，可能瓦解美国数十年构建的伊朗遏制体系。特朗普此前表示愿意与伊朗达成新协议，暗示可能放松部分制裁。此举令欧洲盟友和中东盟国感到不安，担心伊朗利用解除制裁获得的资金扩大地区影响力。以色列和沙特等国已通过外交渠道表达关切。分析人士指出，对伊制裁体系是中东安全架构的基石，任何重大调整都可能引发连锁反应，影响从油价到核不扩散的多个领域。伊朗方面对特朗普的表态持谨慎态度。"),
"Firmus to Build Indonesia Data Center": ("AI初创Firmus携手英伟达在印尼建设数据中心","彭博社报道，澳大利亚AI初创公司Firmus计划与英伟达合作在印尼建设AI数据中心，将部署英伟达最新GPU集群为东南亚客户提供AI算力服务。印尼是东南亚最大数字经济体，AI应用需求快速增长，但本地算力基础设施不足。Firmus选择印尼作为区域扩张首站，看中其市场规模和政策红利。印尼政府正推动数字基础设施建设，为外资数据中心项目提供税收优惠。此举将帮助东南亚企业降低AI算力获取成本，减少对美国和新加坡算力服务的依赖，促进区域AI生态发展。"),
"Apple's Sweeping Price Increases": ("苹果全面涨价，AI时代成本传导至消费者","彭博社报道，苹果公司宣布全线产品涨价，涵盖iPad、Mac和配件产品，涨幅5-15%不等。这是AI时代成本传导至消费者的标志性事件。AI芯片采购成本上涨、关税压力和供应链重组共同推高了苹果的制造成本。分析人士指出，苹果凭借品牌溢价能力能够转嫁部分成本，但持续涨价可能侵蚀新兴市场份额。iPhone虽未在本轮涨价范围内，但市场预期下一代iPhone也将面临定价上调压力。投资者关注涨价对销量的影响，以及苹果AI功能升级能否支撑更高的价格定位。"),
"Austria urges Europe to host Anthropic": ("奥地利呼吁欧洲接待Anthropic，应对美国AI访问限制","路透社报道，奥地利敦促欧洲国家接待AI公司Anthropic在欧洲设立总部，以应对美国对AI模型访问的限制措施。美国政府近期对前沿AI模型实施安全审查，限制了部分欧洲用户的访问权限。奥地利认为，欧洲需要建立自主的AI能力，减少对美国技术的依赖。此举反映了欧盟在AI领域的战略自主诉求。法国和德国此前已表达过类似意愿。分析人士指出，Anthropic若在欧洲设立分支机构，需要遵守欧盟AI法案，可能面临不同的监管环境，但也能获得欧洲市场准入和人才资源。"),
"Mexico, U.S. reopen sterile fly plant": ("美墨重启绝育蝇工厂，应对螺旋蝇虫害阻断牲畜贸易","美联社报道，墨西哥与美国重新开放绝育蝇培育工厂，以应对螺旋蝇虫害爆发对牲畜贸易的严重干扰。虫害已导致美墨边境牲畜贸易暂停，造成数百万美元经济损失。绝育蝇技术通过释放经辐射处理的雄性不育蝇来抑制野生种群繁殖，是控制螺旋蝇最有效的生物防治手段。工厂此前因运营问题关闭，此次重启获得了美国农业部资金支持。两国农业部门强调，虫害防控需要持续投入，中断可能导致螺旋蝇重新入侵美国南部各州，威胁整个北美畜牧业安全。"),
"AI Startup Challenging Tesla and Waymo": ("挑战特斯拉和Waymo：AI初创公司加入自动驾驶竞赛","华尔街日报报道，一家AI初创公司正挑战特斯拉和Waymo在自动驾驶领域的领先地位。该公司采用不同于特斯拉纯视觉方案和Waymo多传感器融合的技术路线，声称能以更低成本实现同等安全水平的自动驾驶。自动驾驶是AI最大的商业化应用场景之一，市场规模预计达数千亿美元。然而，技术门槛、监管审批和公众接受度仍是行业面临的共同挑战。分析人士指出，自动驾驶领域的竞争正从技术验证阶段进入商业化落地阶段，成本效率和场景适应性将成为关键竞争维度。"),
"Japan and South Korea step up defense": ("日韩加强防务装备合作","日经亚洲报道，日本和韩国正加强防务装备领域的合作，包括联合研发和装备互操作性提升。两国正探讨在雷达系统、海军装备和导弹防御方面的技术共享。这是韩日安全合作从情报共享向实质性装备合作升级的重要标志。美国对这一进展表示欢迎，认为其有助于强化三边安全同盟。分析人士指出，防务装备合作面临技术保密和工业利益分配等复杂问题，但面对朝鲜核威胁和中国军事扩张的共同压力，两国预计将逐步深化合作。"),
"Japan and South Korea expand joint": ("日韩扩大联合海上救援演习","日经亚洲报道，日本和韩国正扩大联合海上救援演习的范围和频率。演习涵盖搜救、海事安全和灾难响应等场景，旨在提升两国海军在紧急情况下的协同能力。演习区域从日本海扩展到东海和太平洋海域。此举是韩日安全合作深化的又一举措，反映出两国面对地区安全挑战正逐步克服历史隔阂。海上救援是风险较低的合作领域，适合作为军事互信建设的切入点。分析人士认为，此类功能性合作有助于为更深层次的防务合作铺路，但全面军事同盟仍面临政治和民意制约。"),
"The Week in Numbers: Micron": ("本周数字：美光股价攀升，苹果上调价格","路透社本周数字回顾，聚焦两条科技产业关键动态：美光科技股价因AI内存芯片需求强劲而攀升，苹果则宣布全线产品涨价。美光作为全球第三大存储芯片制造商，正受益于AI服务器对高带宽内存（HBM）的爆发性需求。公司最新季度财报显示营收和利润均超预期。苹果涨价则反映了AI成本向消费端的传导。两条动态共同描绘了AI产业链的价值分配格局——上游芯片商赚取超额利润，下游终端厂商和消费者承担成本。分析人士预计这一趋势将持续至2027年。"),
}

def find_new(title_en):
    t = normalize(title_en)
    for prefix, (title_zh, summary_zh) in NEW.items():
        if t.startswith(normalize(prefix)):
            return title_zh, summary_zh
    return None, None

# 处理每篇文章
sections = {'tech':[], 'americas':[], 'asia_pacific':[]}
translated = 0
missing = []

for a in articles:
    # 跳过无关
    if 'white house park' in a['title_en'].lower():
        continue
    title_zh, summary_zh = find_new(a['title_en'])
    if not title_zh:
        title_zh, summary_zh = find_old(a['title_en'])
    if title_zh:
        a['title_zh'] = title_zh
        a['summary_zh'] = summary_zh
        sections[a['section']].append(a)
        translated += 1
    else:
        missing.append(a['title_en'])

print(f"翻译完成: {translated}条, 未匹配: {len(missing)}")
for m in missing:
    print(f"  ✗ {m[:80]}")

# 生成最终JSON
beijing_tz = timezone(timedelta(hours=8))
now = datetime.now(beijing_tz)
daily = {
    'date': now.strftime('%Y-%m-%d'),
    'updated_at': now.strftime('%Y-%m-%d %H:%M 北京时间'),
    'total': translated,
    'sections': {},
}
for sk, sn in SECTION_NAMES.items():
    sa = sections[sk]
    daily['sections'][sk] = {'name':sn,'count':len(sa),'articles':[]}
    for a in sa:
        daily['sections'][sk]['articles'].append({
            'id':a['id'],'title_zh':a['title_zh'],'summary_zh':a['summary_zh'],
            'title_en':a['title_en'],'source':a['source'],'url':a['url'],
            'published':a.get('published_display',''),
        })

path = f'/workspace/news-hub/data/{now.strftime("%Y-%m-%d")}.json'
with open(path,'w',encoding='utf-8') as f:
    json.dump(daily,f,ensure_ascii=False,indent=2)
print(f"\n已保存: {path}")
for sk,sv in daily['sections'].items():
    print(f"  {sv['name']}: {sv['count']}条")
