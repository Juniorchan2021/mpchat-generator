"""
MPChat v3.0 — 场景 / 卖点 / 文风 / 关键词数据模块
"""

# ══════════════════════════════════════════════════════════════════════════════
# 场景分类 + 32 个细分场景
# ══════════════════════════════════════════════════════════════════════════════

SCENARIO_CATEGORIES = {
    "💳 U卡订阅服务": [
        {
            "label": "用USDT订阅ChatGPT Plus",
            "audience_tag": "AI工具用户",
            "keywords": "USDT订阅ChatGPT, 加密货币充值AI, MP Card订阅, 虚拟信用卡ChatGPT",
            "selling_points": ["virtual_card", "instant_settlement", "subscription_mgmt"],
            "style_hint": "tutorial",
            "pixabay_terms": ["artificial intelligence", "chatbot technology"],
        },
        {
            "label": "用USDT订阅Netflix/Spotify",
            "audience_tag": "流媒体用户",
            "keywords": "USDT充值Netflix, 加密货币订阅Spotify, 虚拟卡流媒体, 海外订阅",
            "selling_points": ["virtual_card", "instant_settlement", "subscription_mgmt"],
            "style_hint": "tutorial",
            "pixabay_terms": ["streaming entertainment", "music headphones"],
        },
        {
            "label": "用USDT续费Apple Developer",
            "audience_tag": "独立开发者",
            "keywords": "USDT续费Apple, 加密货币Apple Developer, MP Card开发者, 虚拟信用卡订阅",
            "selling_points": ["virtual_card", "subscription_mgmt", "multi_currency"],
            "style_hint": "tutorial",
            "pixabay_terms": ["app development", "programming laptop"],
        },
        {
            "label": "用USDT充值Steam游戏",
            "audience_tag": "游戏玩家",
            "keywords": "USDT充值Steam, 加密货币买游戏, 虚拟卡Steam, 比特币游戏充值",
            "selling_points": ["virtual_card", "instant_settlement"],
            "style_hint": "tutorial",
            "pixabay_terms": ["gaming computer", "video game controller"],
        },
    ],
    "🌍 跨境支付与收款": [
        {
            "label": "海外自由职业者收款",
            "audience_tag": "自由职业者",
            "keywords": "自由职业者跨境收款, USDT收款, 海外freelancer收入, 加密货币工资",
            "selling_points": ["virtual_bank_acct", "fiat_onoff", "multi_currency"],
            "style_hint": "pain_story",
            "pixabay_terms": ["freelancer laptop", "remote work coffee"],
        },
        {
            "label": "跨境电商收付款",
            "audience_tag": "跨境卖家",
            "keywords": "跨境电商收款, 稳定币B2B支付, USDT商户收款, 外贸结算",
            "selling_points": ["virtual_bank_acct", "fiat_onoff", "psp_capability"],
            "style_hint": "industry",
            "pixabay_terms": ["ecommerce shipping", "global trade"],
        },
        {
            "label": "海外房租水电支付",
            "audience_tag": "海外生活者",
            "keywords": "海外租房付款, USDT付房租, 加密货币日常消费, MP Card海外支付",
            "selling_points": ["physical_card", "instant_settlement", "multi_currency"],
            "style_hint": "pain_story",
            "pixabay_terms": ["apartment rental", "utility bills"],
        },
        {
            "label": "留学生学费支付",
            "audience_tag": "留学生",
            "keywords": "留学学费支付, USDT交学费, 加密货币汇款学费, 跨境教育支付",
            "selling_points": ["virtual_bank_acct", "fiat_onoff", "multi_currency"],
            "style_hint": "tutorial",
            "pixabay_terms": ["university campus", "student studying"],
        },
    ],
    "🏝️ 数字游民生活": [
        {
            "label": "巴厘岛数字游民日常",
            "audience_tag": "东南亚数字游民",
            "keywords": "巴厘岛数字游民, 加密货币旅居, MP Card海外消费, 稳定币支付生活费",
            "selling_points": ["physical_card", "instant_settlement", "p2p_transfer"],
            "style_hint": "pain_story",
            "pixabay_terms": ["bali tropical", "digital nomad beach"],
        },
        {
            "label": "清迈远程工作者消费",
            "audience_tag": "泰国远程工作者",
            "keywords": "清迈远程办公, 加密支付泰国, 数字游民清迈, USDT泰铢",
            "selling_points": ["physical_card", "instant_settlement", "multi_currency"],
            "style_hint": "pain_story",
            "pixabay_terms": ["chiang mai temple", "coworking space"],
        },
        {
            "label": "欧洲背包客刷卡",
            "audience_tag": "旅行者",
            "keywords": "欧洲旅行刷卡, 加密货币欧洲消费, 背包客支付, MP Card欧元",
            "selling_points": ["physical_card", "multi_currency", "atm_withdrawal"],
            "style_hint": "listicle",
            "pixabay_terms": ["europe travel backpack", "european city"],
        },
        {
            "label": "迪拜自由区创业者",
            "audience_tag": "中东创业者",
            "keywords": "迪拜加密创业, 自由区公司收款, USDT迪拉姆, 中东加密支付",
            "selling_points": ["virtual_bank_acct", "fiat_onoff", "compliance"],
            "style_hint": "industry",
            "pixabay_terms": ["dubai skyline", "business meeting"],
        },
    ],
    "💸 跨境汇款": [
        {
            "label": "菲佣月汇款回家",
            "audience_tag": "海外劳工",
            "keywords": "菲律宾汇款, 海外劳工转账, USDT跨境汇款, 低手续费汇款",
            "selling_points": ["p2p_transfer", "instant_settlement", "fiat_onoff"],
            "style_hint": "pain_story",
            "pixabay_terms": ["remittance family", "money transfer"],
        },
        {
            "label": "跨境务工汇款省手续费",
            "audience_tag": "跨境务工者",
            "keywords": "跨境汇款省钱, USDT转账零手续费, 加密货币汇款, 打工人汇款",
            "selling_points": ["p2p_transfer", "instant_settlement"],
            "style_hint": "review",
            "pixabay_terms": ["construction worker", "international money"],
        },
        {
            "label": "留学生生活费转账",
            "audience_tag": "留学生家长",
            "keywords": "留学生活费转账, 父母跨境汇款, USDT学生生活费, 低成本汇款",
            "selling_points": ["p2p_transfer", "fiat_onoff", "multi_currency"],
            "style_hint": "tutorial",
            "pixabay_terms": ["student life", "parent child"],
        },
    ],
    "🔗 Web3 / DeFi": [
        {
            "label": "加密OG日常消费",
            "audience_tag": "加密老手",
            "keywords": "加密货币消费, 币圈OG刷卡, USDT日常支付, 加密信用卡",
            "selling_points": ["physical_card", "instant_settlement", "dex_integration"],
            "style_hint": "pain_story",
            "pixabay_terms": ["cryptocurrency bitcoin", "digital finance"],
        },
        {
            "label": "DEX交易一站式管理",
            "audience_tag": "DeFi交易者",
            "keywords": "DEX交易平台, Hyperliquid交易, 去中心化交易, DeFi一站式管理",
            "selling_points": ["dex_integration", "non_custodial", "gas_station"],
            "style_hint": "review",
            "pixabay_terms": ["stock trading screen", "financial technology"],
        },
        {
            "label": "RWA国债链上投资",
            "audience_tag": "DeFi投资者",
            "keywords": "RWA投资, 链上国债, 真实世界资产, DeFi理财",
            "selling_points": ["rwa_investment", "compliance", "custody"],
            "style_hint": "industry",
            "pixabay_terms": ["investment growth", "bonds finance"],
        },
        {
            "label": "NFT社区红包互动",
            "audience_tag": "NFT社区成员",
            "keywords": "加密红包, NFT社群互动, USDT红包, 加密社交",
            "selling_points": ["crypto_red_packet", "group_mgmt", "p2p_transfer"],
            "style_hint": "testimony",
            "pixabay_terms": ["nft digital art", "community social"],
        },
    ],
    "👨‍💻 开发者生态": [
        {
            "label": "MiniApp小程序开发变现",
            "audience_tag": "小程序开发者",
            "keywords": "MiniApp开发, 加密小程序, MPChat开发者, Web3小程序变现",
            "selling_points": ["miniapp_sdk", "payment_api", "psp_capability"],
            "style_hint": "tutorial",
            "pixabay_terms": ["software development", "mobile app coding"],
        },
        {
            "label": "Bot自动化营销",
            "audience_tag": "营销开发者",
            "keywords": "加密Bot开发, 自动化营销机器人, MPChat Bot框架, 社群机器人",
            "selling_points": ["bot_framework", "miniapp_sdk", "group_mgmt"],
            "style_hint": "tutorial",
            "pixabay_terms": ["robot automation", "chatbot ai"],
        },
        {
            "label": "PSP支付接入商户",
            "audience_tag": "商户/企业",
            "keywords": "PSP支付接入, 商户加密收款, 稳定币支付网关, 企业支付API",
            "selling_points": ["psp_capability", "payment_api", "merchant_tools"],
            "style_hint": "industry",
            "pixabay_terms": ["payment terminal", "business pos"],
        },
        {
            "label": "API集成加密支付",
            "audience_tag": "后端开发者",
            "keywords": "加密支付API, USDT支付集成, 区块链支付开发, SDK集成",
            "selling_points": ["payment_api", "miniapp_sdk", "bot_framework"],
            "style_hint": "tutorial",
            "pixabay_terms": ["api code", "developer programming"],
        },
    ],
    "👥 社群与社交": [
        {
            "label": "加密社群管理与红包裂变",
            "audience_tag": "社群运营者",
            "keywords": "加密社群运营, 红包裂变营销, 加密社交管理, 群组运营工具",
            "selling_points": ["group_mgmt", "crypto_red_packet", "e2ee"],
            "style_hint": "tutorial",
            "pixabay_terms": ["community group", "social network"],
        },
        {
            "label": "KOL粉丝打赏与付费群",
            "audience_tag": "KOL/内容创作者",
            "keywords": "KOL打赏, 付费群加密, 粉丝经济USDT, 内容创作者变现",
            "selling_points": ["p2p_transfer", "group_mgmt", "crypto_red_packet"],
            "style_hint": "testimony",
            "pixabay_terms": ["influencer content", "social media creator"],
        },
        {
            "label": "DAO治理与财务管理",
            "audience_tag": "DAO组织者",
            "keywords": "DAO财务管理, 去中心化治理, 加密组织工具, DAO金库管理",
            "selling_points": ["group_mgmt", "compliance", "non_custodial"],
            "style_hint": "industry",
            "pixabay_terms": ["governance meeting", "decentralized network"],
        },
    ],
    "🔒 隐私与安全": [
        {
            "label": "端到端加密通讯替代Telegram",
            "audience_tag": "隐私敏感用户",
            "keywords": "端到端加密聊天, Telegram替代品, E2EE通讯, 安全聊天应用",
            "selling_points": ["e2ee", "privacy_settings", "file_encryption"],
            "style_hint": "review",
            "pixabay_terms": ["encrypted security", "privacy lock"],
        },
        {
            "label": "企业机密文件传输",
            "audience_tag": "企业安全负责人",
            "keywords": "企业加密传输, 机密文件安全, E2EE企业通讯, 安全数据传输",
            "selling_points": ["e2ee", "file_encryption", "privacy_settings"],
            "style_hint": "industry",
            "pixabay_terms": ["cybersecurity shield", "business document"],
        },
        {
            "label": "反审查安全聊天",
            "audience_tag": "新闻工作者/活动人士",
            "keywords": "反审查通讯, 安全聊天工具, 隐私保护App, 加密通讯自由",
            "selling_points": ["e2ee", "privacy_settings", "file_encryption"],
            "style_hint": "news",
            "pixabay_terms": ["freedom speech", "journalist press"],
        },
    ],
    "🏢 企业服务": [
        {
            "label": "跨国企业薪资发放",
            "audience_tag": "HR/财务部门",
            "keywords": "跨国薪资发放, USDT工资支付, 加密货币薪资, 企业跨境付薪",
            "selling_points": ["p2p_transfer", "multi_currency", "virtual_bank_acct"],
            "style_hint": "industry",
            "pixabay_terms": ["payroll business", "office team"],
        },
        {
            "label": "B2B跨境贸易结算",
            "audience_tag": "外贸企业",
            "keywords": "B2B跨境结算, 稳定币贸易, 企业USDT支付, 外贸收付款",
            "selling_points": ["virtual_bank_acct", "fiat_onoff", "psp_capability"],
            "style_hint": "industry",
            "pixabay_terms": ["international trade", "cargo shipping"],
        },
        {
            "label": "企业多币种财务管理",
            "audience_tag": "企业CFO",
            "keywords": "多币种管理, 企业加密财务, 稳定币财资管理, 全球资金池",
            "selling_points": ["multi_currency", "virtual_bank_acct", "compliance"],
            "style_hint": "industry",
            "pixabay_terms": ["finance dashboard", "multi currency"],
        },
    ],
    "📈 热点话题": [
        {
            "label": "2026加密支付趋势",
            "audience_tag": "行业观察者",
            "keywords": "2026加密支付, 加密货币趋势, 稳定币支付未来, 数字支付预测",
            "selling_points": ["instant_settlement", "compliance", "multi_currency"],
            "style_hint": "news",
            "pixabay_terms": ["future technology", "trend graph"],
        },
        {
            "label": "稳定币监管利好分析",
            "audience_tag": "政策关注者",
            "keywords": "稳定币监管, 加密货币合规, MiCA法规, 稳定币政策利好",
            "selling_points": ["compliance", "custody", "fiat_onoff"],
            "style_hint": "news",
            "pixabay_terms": ["regulation law", "government policy"],
        },
        {
            "label": "USDT vs USDC对比",
            "audience_tag": "稳定币用户",
            "keywords": "USDT vs USDC, 稳定币对比, Tether Circle比较, 最佳稳定币",
            "selling_points": ["instant_settlement", "compliance", "fiat_onoff"],
            "style_hint": "review",
            "pixabay_terms": ["comparison chart", "cryptocurrency coin"],
        },
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
# 25+ 卖点子特性，分 5 组
# ══════════════════════════════════════════════════════════════════════════════

SELLING_POINT_GROUPS = {
    "💳 MP Card（全球支付卡）": {
        "virtual_card":       "虚拟卡即时发行（Visa/Mastercard）",
        "physical_card":      "实体卡全球 POS / ATM",
        "instant_settlement": "稳定币→法币即时清算",
        "multi_currency":     "多币种结算（USD/EUR/MXN）",
        "atm_withdrawal":     "全球 ATM 提现",
        "subscription_mgmt":  "订阅服务管理（ChatGPT/Netflix…）",
    },
    "💬 MP Chat（加密社交）": {
        "e2ee":             "端到端加密通讯（E2EE）",
        "crypto_red_packet": "加密红包（USDT/USDC）",
        "p2p_transfer":     "P2P 即时转账",
        "group_mgmt":       "社群治理与权限管理",
        "file_encryption":  "加密文件传输",
        "privacy_settings": "精细化隐私配置",
    },
    "🏦 MP Wallet（合规托管）": {
        "compliance":      "MSB + TCSP 牌照合规",
        "custody":         "HashKey + Cobo 机构级托管",
        "lloyds_insurance": "Lloyd's 数字资产保险",
        "fiat_onoff":      "法币出入金（Swift/ACH/IBAN）",
        "virtual_bank_acct": "虚拟银行账户（USD/EUR/MXN）",
    },
    "🔗 DeFi 生态": {
        "dex_integration": "DEX 接入（Hyperliquid/Raydium）",
        "rwa_investment":  "RWA 真实世界资产投资",
        "non_custodial":   "非托管钱包（Privy）",
        "gas_station":     "Gas Station 免 Gas 体验",
    },
    "⚙️ 开发者平台": {
        "miniapp_sdk":    "MiniApp SDK / 小程序生态",
        "bot_framework":  "Bot 框架（自动化机器人）",
        "psp_capability": "PSP 支付服务商资质",
        "payment_api":    "支付 API / SDK",
        "merchant_tools": "商户管理工具",
    },
}

SP_ID_TO_LABEL = {}
for _group, _items in SELLING_POINT_GROUPS.items():
    SP_ID_TO_LABEL.update(_items)

# ══════════════════════════════════════════════════════════════════════════════
# 7 种文章文风 + 提示词指令
# ══════════════════════════════════════════════════════════════════════════════

ARTICLE_STYLES = {
    "🔥 痛点故事型": {
        "id": "pain_story",
        "desc": "第一/第二人称讲述真实场景，先痛后爽，引发共鸣",
        "instruction": (
            "以第一人称或第二人称讲述一个真实感极强的使用场景故事。"
            "开头描述痛点（如高手续费、等待时间、被拒刷卡），中间引入 MPChat 解决方案，"
            "结尾让读者感受到「爽感」。语言生动、有画面感，像朋友推荐。"
        ),
    },
    "📖 手把手教程型": {
        "id": "tutorial",
        "desc": "分步骤图文教程，教程→引流→推荐产品",
        "instruction": (
            "写一篇结构清晰的分步骤教程。使用「第一步 / 第二步 / 第三步」格式。"
            "每步配有操作说明和注意事项。开头以用户搜索意图切入（如「如何用USDT订阅ChatGPT」），"
            "在步骤中自然引入 MPChat 作为最佳工具，结尾给出完整操作清单。"
            "必须包含至少 5 个步骤。可以使用表格对比不同方案。"
        ),
    },
    "🔍 评测种草型": {
        "id": "review",
        "desc": "客观评测对比，数据说话，种草自然",
        "instruction": (
            "以客观评测者的角度撰写产品对比/体验报告。"
            "包含：评测维度（费用、速度、安全性、易用性）+ 数据表格 + 优缺点总结。"
            "引用具体数据和用户反馈，最终给出推荐结论，自然种草 MPChat。"
            "语言冷静理性，避免过度营销感。"
        ),
    },
    "📊 行业分析型": {
        "id": "industry",
        "desc": "宏观视野，数据引用，专业权威",
        "instruction": (
            "以行业分析师的视角撰写深度分析文章。"
            "引用行业数据（市场规模、增长率、监管动态），分析趋势，"
            "将 MPChat 定位为趋势中的代表性产品。使用专业术语但保持可读性。"
            "包含至少 2 个数据引用和 1 个趋势预测。"
        ),
    },
    "📰 新闻热评型": {
        "id": "news",
        "desc": "紧跟热点，专业点评，蹭流量",
        "instruction": (
            "以新闻评论的形式撰写。开头引用一个近期行业热点事件或政策动态，"
            "中间进行专业分析和解读，自然关联 MPChat 的相关功能。"
            "语言简洁有力，节奏快，适合资讯类平台发布。带有「编辑观点」或「点评」段落。"
        ),
    },
    "🗣️ 用户证言型": {
        "id": "testimony",
        "desc": "真实用户故事，口碑传播，信任感强",
        "instruction": (
            "以用户真实体验的形式撰写。可以是一个虚构但真实感极强的用户故事，"
            "包含用户背景、遇到的问题、发现 MPChat 的过程、使用体验和最终效果。"
            "使用口语化表达，带有个人情感色彩，增强可信度和感染力。"
            "可以引用「用户说」的形式增加真实感。"
        ),
    },
    "📋 清单盘点型": {
        "id": "listicle",
        "desc": "Top-N 盘点格式，易读易传播",
        "instruction": (
            "使用「N个理由/N款工具/N个方法」的清单格式撰写。"
            "每个要点配有小标题 + 简短说明（2-3 句话）。"
            "节奏紧凑，信息密度高，适合社交媒体传播。"
            "MPChat 作为核心推荐项出现在清单中（但不要全部都是 MPChat）。"
            "总数建议 5-10 个要点。"
        ),
    },
}

STYLE_ID_TO_KEY = {v["id"]: k for k, v in ARTICLE_STYLES.items()}

# ══════════════════════════════════════════════════════════════════════════════
# SEO 关键词预设组（15 组）
# ══════════════════════════════════════════════════════════════════════════════

KEYWORD_PRESETS = [
    {
        "label": "加密信用卡",
        "keywords": "加密信用卡, 加密借记卡, USDT信用卡, 币圈信用卡, crypto credit card",
        "difficulty": "medium",
    },
    {
        "label": "USDT支付",
        "keywords": "USDT支付, USDT消费, 稳定币支付, USDT刷卡, USDT payment",
        "difficulty": "medium",
    },
    {
        "label": "跨境汇款",
        "keywords": "跨境汇款, 加密货币转账, USDT汇款, 低手续费汇款, cross-border remittance",
        "difficulty": "high",
    },
    {
        "label": "数字游民工具",
        "keywords": "数字游民工具, 远程工作支付, 全球消费卡, digital nomad banking",
        "difficulty": "low",
    },
    {
        "label": "Web3社交",
        "keywords": "Web3社交, 加密社交App, 去中心化聊天, E2EE通讯, crypto messenger",
        "difficulty": "low",
    },
    {
        "label": "加密红包",
        "keywords": "加密红包, USDT红包, 数字货币红包, crypto red packet",
        "difficulty": "low",
    },
    {
        "label": "虚拟银行账户",
        "keywords": "虚拟银行账户, 加密虚拟账户, 美元虚拟账户, 欧元IBAN账户",
        "difficulty": "medium",
    },
    {
        "label": "RWA投资",
        "keywords": "RWA投资, 真实世界资产, 链上国债, RWA理财, tokenized assets",
        "difficulty": "low",
    },
    {
        "label": "DEX交易",
        "keywords": "DEX交易, 去中心化交易所, Hyperliquid, Raydium, DeFi trading",
        "difficulty": "high",
    },
    {
        "label": "MiniApp开发",
        "keywords": "MiniApp开发, 加密小程序, Web3小程序, MPChat SDK, blockchain miniapp",
        "difficulty": "low",
    },
    {
        "label": "企业加密支付",
        "keywords": "企业加密支付, B2B稳定币, 商户USDT收款, 企业数字资产, business crypto payment",
        "difficulty": "medium",
    },
    {
        "label": "稳定币钱包",
        "keywords": "稳定币钱包, USDT钱包, USDC钱包, 合规加密钱包, stablecoin wallet",
        "difficulty": "high",
    },
    {
        "label": "加密合规",
        "keywords": "加密合规, MSB牌照, 加密货币监管, 合规稳定币, crypto compliance",
        "difficulty": "medium",
    },
    {
        "label": "USDT订阅服务",
        "keywords": "USDT订阅, 加密货币充值, 虚拟卡订阅, USDT买会员, crypto subscription",
        "difficulty": "low",
    },
    {
        "label": "加密隐私通讯",
        "keywords": "加密隐私通讯, E2EE聊天, 安全加密App, 隐私社交, encrypted messaging",
        "difficulty": "low",
    },
]
