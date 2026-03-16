# MPChat 智能软文生成器 — 产品设计说明文档

**版本：v4.1 → v5（迁移中）**
**当前版本：v4.1 (已上线) · v5 (文档阶段)**
**最后更新：2026-03-15**
**开发工具：全部代码（后端逻辑 + Streamlit UI + 工具模块）由 Claude Opus 编写和维护**

---

## 1. 产品定位与目标

### 1.1 产品定位

MPChat 智能软文生成器是一款面向 MPChat 内容营销团队的**内部 SEO 内容生产工具**，专注于为 MPChat（mp.net）生态产品（MP Card、MP Chat、MP Wallet、开发者平台）批量生产高质量、多语言、SEO + GEO 双优化的推广软文，并自动分发到多平台以提升 Google 关键词占有量和 AI 搜索引擎可见性。

### 1.2 核心目标

- 内容生产效率：单篇 < 60 秒，批量 10 篇 < 10 分钟
- 全球市场覆盖：16+ 语言，覆盖亚太 + 发展中国家市场
- Google 关键词占位：200+ 长尾关键词有排名
- AI 搜索可见性：在 ChatGPT / Perplexity / Gemini 中被引用
- 多平台分发：一键发布到 10+ 内容平台

### 1.3 目标用户

本工具的直接用户是 **MPChat 内部内容运营团队**，不面向外部用户。

---

## 2. 产品架构

```
输入层              智能层              输出层              分发层
──────────        ──────────        ──────────        ──────────
场景选择(37+)     SERP 分析器       Module A           Dev.to 直发
卖点配置(25+)     LLM 生成引擎      SEO 元数据         Hashnode 直发
语言选择(16+)     GEO 优化引擎      + A/B 标题         Medium 格式复制
文风选择(7种)     多图库聚合        Module B           LinkedIn 格式复制
SEO 关键词(17+)   知识库            正文 + 文内图       知乎/公众号 格式复制
模式切换(SEO/GEO) AI 人性化引擎     Module C           Twitter 线程拆分
                                    配图 + 提示词       加密博客投稿包
                                    Module D
                                    SEO/GEO 工具箱
                                    + AI 检测
                                    Module E
                                    多平台分发
                                    Module F
                                    外部文章优化检测
```

---

## 3. 功能模块设计

### 3.1 AI 服务商配置

支持 6 家 AI 服务商，下拉选择后自动填充 Base URL 和推荐模型：

- Google Gemini（免费）— gemini-2.5-flash / gemini-2.5-pro
- OpenAI — gpt-4o / gpt-4o-mini
- DeepSeek — deepseek-chat / deepseek-reasoner
- Kimi (月之暗面) — moonshot-v1-128k
- OpenRouter（全模型）— claude / gemini / gpt / deepseek
- 自定义（手动填写）

默认预填 Gemini API Key（可修改），降低使用门槛。

### 3.2 语言选择 (16 种)

Phase 1 — 亚太地区 (10 种)：
中文、英文、日语、韩语、越南语、泰语、印尼语、马来语、菲律宾语、印地语

Phase 2 — 发展中市场 (6 种)：
阿拉伯语、巴西葡萄牙语、拉丁美洲西班牙语、土耳其语、斯瓦希里语、乌尔都语

实现方式：纯 Prompt 工程，每种语言配置语言名称、ISO 代码、LLM 指令、书写方向。

### 3.3 写作场景 (37+ 细分场景，10 大类)

- 💳 U卡订阅服务 (4)：ChatGPT Plus / Netflix / Apple Developer / Steam
- 🌍 跨境支付与收款 (4)：自由职业者 / 跨境电商 / 房租水电 / 留学学费
- 🏝️ 数字游民生活 (4)：巴厘岛 / 清迈 / 欧洲背包客 / 迪拜创业者
- 💸 跨境汇款 (3)：菲佣汇款 / 跨境务工 / 留学生生活费
- 🔗 Web3 / DeFi (4)：加密OG消费 / DEX管理 / RWA投资 / NFT红包
- 👨‍💻 开发者生态 (4)：MiniApp / Bot营销 / PSP接入 / API集成
- 👥 社群与社交 (3)：社群红包裂变 / KOL打赏 / DAO治理
- 🔒 隐私与安全 (3)：替代Telegram / 企业传输 / 反审查
- 🏢 企业服务 (3)：跨国薪资 / B2B结算 / 多币种管理
- 📈 热点话题 (3)：2026趋势 / 稳定币监管 / USDT vs USDC
- ⚔️ 竞品对比 (5)：vs Telegram / vs Binance Card / vs Trust Wallet / vs Signal / vs Crypto.com

### 3.4 主打卖点 (25+ 子特性，5 组)

- 💳 MP Card：虚拟卡、实体卡、即时清算、多币种、ATM提现、订阅管理
- 💬 MP Chat：E2EE、加密红包、P2P转账、社群管理、文件加密、隐私配置
- 🏦 MP Wallet：MSB/TCSP牌照、HashKey/Cobo托管、Lloyd's保险、法币出入金、虚拟银行账户
- 🔗 DeFi 生态：DEX接入、RWA投资、非托管钱包、Gas Station
- ⚙️ 开发者平台：MiniApp SDK、Bot框架、PSP资质、支付API、商户工具

### 3.5 文章文风 (7 种)

- 🔥 痛点故事型：先痛后爽，第一人称，画面感
- 📖 手把手教程型：分步骤，5步以上，操作清单
- 🔍 评测种草型：数据表格，客观评测，冷静推荐
- 📊 行业分析型：数据引用，趋势预测，专业术语
- 📰 新闻热评型：紧跟事件，快节奏，编辑点评
- 🗣️ 用户证言型：口语化，个人情感，真实感
- 📋 清单盘点型：Top-N格式，信息密度高，易传播

### 3.6 配图系统（3 级图源 + 随机化 + 智能搜索）

采用 3 级 fallback 架构 + 双重随机化，确保始终有图可用且每次生成不重复：

**图源架构：**
- **Tier 1 — Pixabay（主图源）**：REST API 搜索，返回高分辨率图片 + 摄影师元数据，100 次/分钟，需 API Key
- **Tier 2 — Pexels（补充图源）**：REST API 搜索，200 次/小时免费额度，需 API Key（可选）
- **Tier 3 — Placewise CDN（兜底）**：URL-based 语义图片服务（`img.placewise.io/800x600-query`），无需 API Key

**随机化机制（v4.1 新增）：**
- 每次 API 请求随机选择 1-5 页结果（`page = random.randint(1, 5)`），避免同一搜索词总返回同样图片
- 请求比实际需要多 4 张（`per_page = count + 4`），从返回池中 `random.shuffle()` 后截取
- 最终合并结果再次 shuffle，确保图片排序每次不同

**智能搜索词策略（v4.1 新增）：**
- **优先级**：AI 生成的 `image_search_terms`（每篇文章独特）> 文章标题关键词提取 > 场景静态 `pixabay_terms`
- **Prompt 强化**：要求 AI 生成 5 个具体的 2-4 词搜索短语（如 `"woman paying coffee smartphone"`），覆盖不同视觉场景（支付/生活方式/科技/人物/城市），禁止 `"crypto"` 等太泛泛的词
- **标题提取**：自动从 `seo_title` 提取前 4 个有效词作为补充搜索词，提升配图与文章内容的相关性

注意：Placewise 是 URL-based CDN 服务（非 REST 搜索 API），通过语义 slug 直接生成图片 URL。

### 3.7 网络知识库

10 源并行爬取（ThreadPoolExecutor）：
mp.net 官网 4 页 + Medium RSS + Twitter + Google/百度/DuckDuckGo + GlobeNewswire
缓存 2 小时，点击「生成」时才触发。

### 3.8 JSON 解析引擎（5 层容错）

1. 直接 json.loads()
2. 修复尾逗号
3. 处理字符串内换行
4. 正则字段提取（处理截断 JSON）
5. 手动清理 + 转义修复

max_tokens = 16384，避免输出截断。

### 3.9 SEO + GEO 双优化引擎

**问题背景：** 单独优化 SEO 可能降低 GEO 评分（如拉长段落增加关键词密度，违反 GEO 短段落要求），反之亦然。

**解决方案：** 联合优化 Prompt 设计，在一次 LLM 调用中同时满足两套评分标准。

**兼容策略（写入 System Prompt）：**
- H2 标题：问句格式（满足 GEO）+ 含目标关键词（满足 SEO）
- 段落：短段落 2-3 句（满足 GEO）+ 自然植入关键词（满足 SEO）
- 数据引用：带出处的统计数据，同时提升 GEO 可信度和 SEO 内容质量
- FAQ 段落：满足 GEO 的 Q&A 结构，同时覆盖 SEO 长尾关键词
- CTA：引导访问 mp.net（SEO 必需），融入 Answer-First 段落（GEO 加分）

**UI 设计：**
- Module D 新增「双优化」Tab，显示 SEO 和 GEO 双评分环
- 仅当任一分数 < 90 时显示「一键双优化到 90+」按钮
- 优化完成后显示优化前后分数对比
- max_tokens = 10000，确保长文章+FAQ 不被截断

### 3.10 三合一优化引擎（SEO + GEO + 人性化）（v4.1 新增）

**问题背景：** 用户使用「一键人性化改写」降低 AI 检测率后，SEO 和 GEO 评分大幅下降（常见降幅 20-40 分）。三项指标互相冲突：人性化打破结构 → SEO/GEO 分数崩塌。

**根因分析：**
- 原人性化 Prompt 仅模糊要求"保持 SEO 质量"，未明确列出不可删除的结构元素
- LLM 为了降低 AI 感，会移除 H2 标题结构、FAQ 段落、数据引用、关键词密度等 SEO/GEO 关键元素

**解决方案：三层约束架构**

```
A 层 — SEO 硬性约束（结构层，不可删减）
├── H1/H2 标题结构 + 关键词
├── 关键词密度 1-2%
├── CTA（引导 mp.net）
└── 800-1200 字

B 层 — GEO 硬性约束（结构层，不可删减）
├── Answer-First 开头
├── 问句 H2 ≥ 30%
├── 数据引用 5+
├── 权威引用 3+
├── 实体一致性
└── FAQ 段落 5 个 Q&A

C 层 — 人性化（在 A/B 框架内改写风格）
├── 口语化叙述、第一人称
├── 场景故事细节
├── 打破 AI 固定句式
├── 句子长度变化
├── 感叹句/反问句
├── 数据引用人性化包裹
└── H2 标题个性化
```

**兼容策略（D 层）：**
- H2 = 问句（GEO）+ 含关键词（SEO）+ 口语化（人性化）
- 数据引用 = 带来源（GEO）+ 个人化表述包裹（人性化）
- FAQ = 结构化 Q&A（GEO/SEO）+ 答案用口语写（人性化）
- CTA = 明确行动引导（SEO）+ 第一人称推荐语气（人性化）

**UI 设计：**
- Module D「AI 检测」Tab 内，「人性化改写」和「三合一优化」并排两个按钮
- 「人性化改写」：仅降低 AI 检测率，保留 SEO/GEO 结构（改进后的 Prompt）
- 「三合一优化」：一次 LLM 调用同时达成 SEO ≥ 90 + GEO ≥ 90 + AI 检测率 ≤ 30

**影响文件：** `geo_tools.py`（新增 `build_triple_optimize_prompt()`）、`app.py`（AI 检测 Tab 重构）

### 3.11 官网 URL 统一（v4.1 修复）

**问题背景：** 产品知识库 `knowledge.txt` 中的官网写为 `mpchat.io`（旧域名），导致 AI 生成的文章 CTA 推的是错误网址。

**修复范围：**
- `knowledge.txt`：品牌定位和 CTA 段落的官网 URL
- `app.py` 系统 Prompt：CTA 指令明确标注"官网是 mp.net，不是 mpchat.io"
- `app.py` SEO 优化 / 人性化 Prompt：CTA 引用
- `geo_tools.py`：双优化和三合一优化的 CTA 指令
- `seo_tools.py`：内部链接基础 URL（原本已正确指向 mp.net）

---

## 4. 输出模块

### Module A — SEO 元数据

- SEO Title（50-60 字符）+ 字符数统计
- Meta Description（120-160 字符）+ 字符数统计
- URL Slug（英文路径）
- A/B 备选标题（3 个不同角度），一键「采用」
- 一键复制元数据

### Module B — 正文内容

- Markdown 渲染，Pixabay/Pexels/Unsplash 图片通过 st.image() 内嵌在 H2 后
- 导出 Markdown / HTML / 纯文本
- HTML 导出使用 markdown 库正确转换（支持表格、代码块、图片）

### Module C — 文章配图

- 多图库实图（最多 8 张，4 列网格）
- AI 配图提示词（2-3 个场景）
- 无图片时显示诊断信息

### Module D — SEO / GEO 工具箱

Tab 1: Schema JSON-LD（Article + FAQPage + Organization）
Tab 2: 内部链接（基于卖点自动生成）
Tab 3: SEO 评分（0-100）+ 一键 SEO 优化
Tab 4: GEO 评分（0-100）+ 一键 GEO 优化
Tab 5: SEO + GEO 双优化（见 3.9）
Tab 6: AI 内容检测 + 人性化改写 + 三合一优化（见 3.10）

### Module E — 多平台分发

API 直发：Dev.to / Hashnode
格式复制：Medium / LinkedIn / Twitter 线程 / 知乎 / 微信公众号 / 加密博客投稿

---

## 5. GEO 优化规范

当 GEO 模式开启时，遵循以下规范：

- Answer-First：开头 40-100 字直接回答核心问题（引用率 +27%）
- 问题式标题：30%+ 的 H2 用问句
- 数据引用：5+ 个带来源的统计数据（引用率 +40%）
- FAQ 段落：5 个 Q&A 对，每答案 < 100 字
- 短段落：每段 2-3 句
- 权威引用："据...研究显示"框架（可信度 +32%）
- 实体一致性：MPChat / MP Card 全文统一命名

---

## 6. 文件结构

### 6.1 v4.x（Streamlit 单体，当前线上版本）

```
MPChat-软文机器人/
├── app.py              # Streamlit 主应用（UI + 业务逻辑）
├── scenarios.py         # 场景/卖点/文风/关键词/语言数据
├── image_client.py      # 多图库聚合（Pixabay + Pexels + Placewise）
├── seo_tools.py         # SEO 工具（评分、Schema、Slug、内链）
├── geo_tools.py         # GEO 评分 + Schema + Prompt 构建
├── publishers.py        # 多平台发布格式化 + API 集成
├── serp_analyzer.py     # SERP 竞品分析器
├── knowledge.txt        # MPChat 产品知识库
├── requirements.txt     # Python 依赖
├── packages.txt         # 系统级依赖
├── .env.example         # 环境变量示例
├── PRD.md               # 产品需求文档
├── DESIGN_SYSTEM.md     # 设计规范文档（Apple HIG）
├── MIGRATION_PLAN.md    # v5 迁移方案
├── ENGINEERING_GUIDE.md # 工程规范文档
└── .gitignore
```

### 6.2 v5（前后端分离，迁移目标）

```
MPChat-软文机器人/
├── api/                        # Python 后端（FastAPI）
│   ├── main.py                 # FastAPI 入口 + CORS
│   ├── routers/                # 按模块拆分的子路由
│   │   ├── config.py           # /api/v1/config/*（服务商、场景）
│   │   ├── generate.py         # /api/v1/generate（单篇 + 批量）
│   │   ├── analyze.py          # /api/v1/analyze/*（SEO、GEO）
│   │   ├── optimize.py         # /api/v1/optimize（一键优化）
│   │   ├── external.py         # /api/v1/external/*（外部文章）
│   │   ├── publish.py          # /api/v1/publish/*（多平台分发）
│   │   └── tools.py            # /api/v1/schema, /api/v1/slug, /api/v1/links
│   └── models/                 # Pydantic 请求/响应模型
│       ├── requests.py
│       └── responses.py
├── frontend/                   # Next.js 前端
│   ├── app/                    # App Router 页面
│   │   ├── page.tsx            # / — 创作工作台
│   │   ├── external/page.tsx   # /external — 外部文章优化
│   │   └── history/page.tsx    # /history — 生成历史
│   ├── components/
│   │   ├── ui/                 # 通用 UI 组件（Button、Card、Tab 等）
│   │   └── features/           # 业务组件（ConfigBar、ScoreRing 等）
│   ├── lib/
│   │   └── api.ts              # 后端 API 调用封装
│   ├── styles/
│   │   └── globals.css         # Tailwind + Apple HIG CSS 变量
│   ├── tailwind.config.ts
│   └── package.json
├── core/                       # 共享 Python 模块（包）
│   ├── __init__.py
│   ├── scenarios.py            # 场景/卖点/文风/关键词/语言
│   ├── image_client.py         # 多图库聚合
│   ├── seo_tools.py            # SEO 工具
│   ├── geo_tools.py            # GEO 工具
│   ├── publishers.py           # 多平台分发
│   ├── serp_analyzer.py        # SERP 分析
│   └── knowledge.txt           # 产品知识库
├── tests/                      # 测试
├── requirements.txt            # 后端 Python 依赖
├── PRD.md                      # 产品需求文档
├── DESIGN_SYSTEM.md            # 设计规范（Apple HIG）
├── MIGRATION_PLAN.md           # 迁移方案
├── ENGINEERING_GUIDE.md        # 工程规范
└── .gitignore
```

---

## 7. 实施路线图

| 阶段 | 功能 | 预计时间 |
|---|---|---|
| Phase 1 | 16 种语言 + 多图库聚合 | 0.5 天 |
| Phase 2 | AI 内容检测 + 人性化改写 | 1 天 |
| Phase 3 | GEO 优化模式 + 评分 + FAQ Schema | 1.5 天 |
| Phase 4 | Module E 多平台分发 | 2 天 |
| Phase 5 | SERP 分析器 | 1.5 天 |
| **总计** | | **约 6.5 天** |

---

## 8. 竞品差异化

核心竞争优势：
1. 唯一的产品专属 AI 软文工具（非通用写作工具）
2. SEO + GEO 双优化
3. 零成本（自备 LLM API Key）
4. 多平台分发闭环（生成 → 格式化 → 发布）
5. 3 级图源 fallback（Pixabay → Pexels → Placewise CDN）
6. 5 层容错 JSON 解析
7. 37+ 深度定制场景

---

## 9. 已知问题与修复记录 (v4.0.1)

### 9.1 配图无法加载（v4.0 → v4.0.1 修复）

**问题描述：** 启用「获取配图」开关后，Module C 显示「未获取到图片」，文章正文无配图。

**根因分析：**
- `image_client.py` 调用 `https://placewise.io/api/v1/search`，但该 REST API 端点不存在
- Placewise 实际上是 URL-based CDN 服务，正确用法是 `https://img.placewise.io/800x600-query`
- Placewise 搜索永远返回空结果 → 触发 Pixabay fallback → Pixabay 如果也失败则 0 图

**修复方案：** 重构为 3 级 fallback 架构
1. Tier 1: Pixabay REST API 搜索（主图源，v3.1 已验证可用）
2. Tier 2: Pexels REST API 搜索（补充图源，可选 API Key）
3. Tier 3: Placewise CDN URL 构建（兜底，无需 API Key）

**影响文件：** `image_client.py`, `app.py`（侧边栏新增 Pexels Key 输入）

### 9.2 SEO/GEO 优化按钮无响应（v4.0 → v4.0.1 修复 → v4.1 重构）

**问题描述（v4.0）：** 点击「一键 SEO 优化到 90+」后，加载动画出现但页面无变化。

**v4.0.1 修复（延迟 rerun）：** 使用 `_pending_rerun` flag + 顶层 `st.rerun()` 延迟刷新。

**v4.1 问题（Tab 跳转）：** 延迟 rerun 虽然解决了按钮无响应，但 `st.rerun()` 会重置所有 Tab 到第一个（Schema），导致用户点击 AI 检测 / 人性化后页面跳到 Schema Tab，体验极差。

**v4.1 最终方案：完全移除 st.rerun()**
1. 移除全局 `_pending_rerun` flag 和 `st.rerun()` 调用
2. 所有优化按钮（SEO / GEO / 双优化 / 人性化 / 三合一）完成后，只更新 `st.session_state` 中的文章内容 + 显示 `st.success()` 消息
3. 用户停留在当前 Tab，下次切换 Tab 或点击任何控件时自动看到更新后的内容
4. Tab 状态不再被重置，交互体验大幅改善

**影响文件：** `app.py`（移除 4 处 `_pending_rerun = True` 和 1 处全局 rerun 检查）

### 9.3 API Key 安全存储（v4.0 → v4.0.1 修复）

**问题描述：** Gemini API Key 硬编码在源码中，推送到 GitHub 后被 Google 自动扫描吊销。

**修复方案：**
1. 从代码中移除所有明文 API Key
2. 使用 `st.secrets["GEMINI_API_KEY"]` 从 Streamlit Cloud Secrets 安全读取
3. 回退到 `os.getenv("OPENAI_API_KEY")` 支持本地开发
4. 用户可在侧边栏手动输入覆盖

---

## 10. Stripe × Apple UI/UX 重构 (v4.1 已实施)

> **注意：本章描述的是 v4.1 Streamlit 版本的 UI 实现。v5 前后端分离版本将采用全新的 Apple HIG 设计系统，详见 [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)。本章保留作为历史参考。**

v4.1 对整个 UI 进行了彻底重构，设计灵感来自 Stripe Dashboard（交互 & 配色）+ Apple（字体 & 排版），使用 MP.NET 官方品牌元素。

### 10.1 字体系统

```css
font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
             "Helvetica Neue", Arial, sans-serif;
```
- 使用 Apple SF Pro 系统字体栈（macOS/iOS 原生渲染，零加载延迟）
- 移除 Google Fonts 的 Inter 字体（减少外部请求，加快首屏渲染）
- 启用 `-webkit-font-smoothing: antialiased` 提升暗色背景上的文字清晰度

### 10.2 配色方案（Hybrid：MP.NET 黑底 + Stripe 蓝紫渐变）

| 元素 | 色值 |
|---|---|
| 背景 | `#09090B`（近黑） |
| 侧边栏背景 | `#0C0C0F` |
| 卡片背景 | `rgba(17,17,21,0.8)` + `backdrop-filter: blur(16px)` |
| 主强调色 | `#635BFF`（Stripe Blurple） |
| 渐变高光 | `linear-gradient(135deg, #635BFF, #0096FF)` |
| 文字主色 | `#FAFAFA` |
| 文字辅色 | `#A1A1AA` |
| 文字弱色 | `#71717A` |
| 边框 | `rgba(255,255,255,0.06)` |
| 背景光效 | 双层径向渐变（蓝紫 + 青色弥散光） |

### 10.3 品牌元素

- **Banner**：MP.NET 官方 Logo（`https://mp.net/Logo.png`，44px 高）+ 蓝紫渐变标题文字 + Stripe 风格版本徽章
- **侧边栏顶部**：小尺寸 MP.NET Logo（28px）
- **侧边栏底部**：MP.NET Logo + 版本号 footer

### 10.4 侧边栏重构（扁平分区布局）

**重大变更：** 彻底移除所有 `st.expander()` 折叠组件。

原因：Streamlit 的 expander 在暗色主题下折叠/展开行为不稳定，且默认折叠导致 API Key 等关键配置不可见。

新结构：
```
[MP.NET Logo]
─── AI 服务商（section header）
    selectbox + text_input × 2 + selectbox
─── 优化模式
    radio (SEO / SEO+GEO)
─── 配图
    toggle + conditional key inputs
─── 数据源
    SERP toggle + 网络知识库 toggle
─── 多平台分发
    Dev.to / Hashnode / Publication ID
─── Footer (logo + version)
```

- 用 `st.divider()` + 自定义 CSS section header（`0.7rem, uppercase, #71717A`）分隔区块
- 所有配置项始终可见，无需折叠展开
- Radio 选项使用 pill 样式（CSS 圆角卡片 + hover 高光）

### 10.5 组件样式

- **卡片**：毛玻璃效果 `backdrop-filter: blur(16px)`，hover 时边框变蓝紫色
- **按钮**：Stripe 风格渐变 `#635BFF → #5046E5`，hover 上浮 1px + 阴影增强
- **输入框**：深色内嵌背景，focus 时 2px 蓝紫色光环
- **Tabs**：Stripe Dashboard 胶囊标签页，选中态蓝紫半透明背景
- **评分环**：60px 圆形 + `inset box-shadow` 描边

### 10.6 Streamlit 隐藏元素策略

```css
#MainMenu { visibility: hidden; }           /* 汉堡菜单 */
footer { visibility: hidden; }              /* Streamlit 水印 */
header { background: transparent; }         /* 顶栏透明化 */
[data-testid="collapsedControl"] { visible } /* 保留侧边栏切换按钮 */
```

注意：不能隐藏 `header`（会连带隐藏侧边栏切换按钮），只能设透明背景。

---

## 11. v4.1 修复记录

### 11.1 优化按钮导致 Tab 跳转（v4.0.1 → v4.1）

见 9.2 更新说明。

### 11.2 人性化改写破坏 SEO/GEO 评分（v4.1 新增）

**问题描述：** 使用「一键人性化改写」后，SEO 评分从 90 降到 60，GEO 从 88 降到 50。

**根因：** 人性化 Prompt 过于宽泛（"保持 SEO 质量"），LLM 为降低 AI 感删除了 H2 结构、FAQ、数据引用等 SEO/GEO 核心元素。

**修复方案：**
1. 改进人性化 Prompt：明确列出 7 项不可删除的结构元素（H1/H2、关键词、FAQ、CTA、数据引用、实体名、权威来源）
2. 改进 system message：强调"只改写行文风格，保留所有结构"
3. 新增三合一优化按钮（见 3.10）

**影响文件：** `app.py`（AI 检测 Tab 重构）、`geo_tools.py`（新增 `build_triple_optimize_prompt()`）

### 11.3 配图重复且不相关（v4.1 新增）

**问题描述：** 同一场景多次生成文章，配图完全相同；部分配图与文章内容不相关。

**根因：**
- Pixabay/Pexels API 每次请求 page=1，同搜索词返回同结果
- 搜索词优先使用场景静态 `pixabay_terms`（如 "artificial intelligence"），太泛泛
- AI 生成的 `image_search_terms` 被排在后面，且 Prompt 未要求具体性

**修复方案：** 见 3.6 更新说明（随机页码 + shuffle + AI 优先搜索词 + 标题提取 + Prompt 强化）。

**影响文件：** `image_client.py`（核心逻辑重构）、`app.py`（传入 article_title + 改进搜索词 Prompt）

### 11.4 CTA 推广错误网址（v4.1 新增）

**问题描述：** 生成的文章 CTA 推的是 `mpchat.io`（旧域名），而非正确的 `mp.net`。

**根因：** `knowledge.txt` 产品知识库中官网写为 `mpchat.io`。

**修复方案：** 见 3.11 说明。

**影响文件：** `knowledge.txt`、`app.py`、`geo_tools.py`

---

## 12. Module F — 外部文章优化检测 (v4.1 新增)

### 12.1 功能背景

MPChat 团队除了使用本工具生成软文外，还在 mp.net 官方博客和其他渠道发布人工撰写的文章。这些外部文章同样需要 SEO/GEO 优化和 AI 检测，但此前所有优化工具均绑定在生成流程中（必须先用本工具生成文章才能使用评分和优化功能）。

### 12.2 功能定位

Module F 是一个**独立于生成流程**的文章优化检测工具，用户可将任意来源的文章粘贴进来，使用完整的 SEO/GEO/AI 检测/人性化/三合一优化工具链。

### 12.3 UI 设计

Module F 位于批量生成模块之后、单篇生成输出之前，作为 `st.expander` 始终可见（`expanded=False`）。

**输入区域：**
- 文章内容文本框（`st.text_area`，Markdown 格式，300px 高度）
- 目标关键词输入（`st.text_input`，逗号分隔，可选）
- 「开始分析」按钮和「清空」按钮

**分析结果（4 个 Tab）：**

| Tab | 功能 | 对应工具函数 |
|-----|------|------------|
| 📊 SEO 评分 | 字数/阅读时间/H2数/评分环 + 关键词密度 + 一键 SEO 优化 | `reading_stats()` |
| 🧠 GEO 评分 | 评分环 + 6 项详细指标表 + 问题/建议 + 一键 GEO 优化 | `geo_score()` |
| ⚡ 双优化 | SEO + GEO 双评分环 + 一键联合优化 | `build_dual_optimize_prompt()` |
| 🤖 AI 检测 | AI 痕迹检测 + 人性化改写 + 三合一优化 | `build_triple_optimize_prompt()` |

**优化结果展示区（v4.1 UX 升级）：**

优化操作完成后，在 Tab 下方自动展示结果区块，包含三部分：

1. **评分对比卡片** — 两列显示优化前/后的 SEO 和 GEO 评分，用绿色/红色箭头标注分数变化（如 `50 → 92 ↑42`）
2. **修改说明列表** — LLM 逐条输出具体改了什么，用颜色标签区分类型：
   - 绿色 `[新增]` — 新增内容（H2 段落、FAQ、CTA 等）
   - 蓝色 `[优化]` — 改写优化（关键词密度、段落精简等）
   - 橙色 `[调整]` — 结构调整（段落拆分、顺序变化等）
3. **优化后全文预览** — 渲染完整 Markdown 文章供用户阅读
4. **操作按钮** — 「下载优化后文章」（.md 文件）、「撤销优化，恢复原文」、代码视图（方便复制）

**JSON 输出格式：** 所有优化 prompt 要求 LLM 以 JSON 返回：
```json
{
  "optimized_article": "完整 Markdown 文章",
  "changelog": ["修改说明1", "修改说明2", "..."]
}
```
解析时使用多策略兜底（直接解析 → 修复尾逗号 → 正则提取），若全部失败则将原始输出作为纯文章处理。

### 12.4 状态管理

Module F 使用独立的 session state key，避免与生成流程冲突：

| Key | 用途 |
|-----|------|
| `ext_article` | 当前文章内容（优化后自动更新） |
| `ext_original` | 用户最初粘贴的原文（不随优化改变，用于撤销恢复） |
| `ext_keywords` | 当前目标关键词 |
| `ext_detect_result` | AI 检测结果缓存 |
| `ext_changelog` | 最近一次优化的修改说明列表 |
| `ext_score_before` | 优化前的 SEO/GEO 评分（用于对比展示） |
| `ext_opt_type` | 最近一次优化的类型标签（如「SEO 优化」「三合一优化」） |

### 12.5 与 Module D 的差异

- **无 Schema/内链 Tab**：外部文章不需要 mp.net 特定的 JSON-LD Schema 或内部链接建议
- **独立状态**：所有按钮 key 加 `ext_` 前缀，状态互不影响
- **FAQ 默认为空**：外部文章无法自动提取 FAQ pairs，`geo_score()` 传入空列表
- **通用 CTA**：SEO 优化 prompt 使用 `mp.net` 作为 CTA 目标，但不强制 MPChat 产品线
- **修改说明 + 对比视图**：Module D 仅显示 `st.success()`，Module F 完整展示 changelog 和前后评分对比
- **撤销恢复**：Module F 保留原文，支持一键回退；Module D 直接覆盖 `last_result`

### 12.6 影响文件

- `app.py`：Module F section（~400 行），含 helper 函数 `_parse_opt_result()`、`_render_changelog()`、`_render_score_comparison()`、`_ext_run_optimize()`

---

## 13. v5 架构升级 — 前后端分离

### 13.1 升级背景

v4.x 基于 Streamlit 构建，优势在于快速原型、零前端代码即可上线，但随着功能不断迭代（37+ 场景、多模块输出、多平台分发），Streamlit 的局限性日益明显：

| 痛点 | 说明 |
|------|------|
| 自定义 UI 受限 | 无法实现精细动画、拖拽交互、响应式多栏布局；CSS 注入受 Shadow DOM 限制 |
| 首屏加载慢 | Python 服务端渲染，每次交互全量 rerun，连接不稳时出现白屏/断连 |
| 组件生态有限 | 缺少成熟的富文本编辑器、Markdown 实时预览、评分可视化等高阶组件 |
| SEO 不友好 | Streamlit 生成的 SPA 无法被搜索引擎索引（如有对外展示需求） |
| 部署绑定 | 目前仅能部署在 Streamlit Cloud，不支持 CDN 加速 |

### 13.2 目标架构

```
用户浏览器
   │
   ▼
┌──────────────────┐         ┌──────────────────┐
│  Next.js 前端     │  HTTPS  │  FastAPI 后端      │
│  Cloudflare Pages │ ◄─────► │  Railway / Render │
│  (SSG + CSR)     │  JSON   │  (Python 3.11+)   │
└──────────────────┘         └──────────────────┘
                                     │
                              ┌──────┴──────┐
                              ▼             ▼
                         LLM APIs     图库 APIs
                     (OpenAI/Gemini)  (Pixabay/Pexels)
```

- **前端**：Next.js 14+ App Router，部署于 Cloudflare Pages（免费额度：无限带宽，500 次/月构建）
- **后端**：FastAPI，部署于 Railway / Render（免费额度足够开发和轻度使用）
- **通信**：前端通过 `fetch` / `SWR` 调用后端 REST API，JSON 格式

### 13.3 用户体验变化

| 维度 | v4.x (Streamlit) | v5 (Next.js + FastAPI) |
|------|-------------------|------------------------|
| 首屏加载 | 3-5s（Python SSR） | <1s（静态 HTML + CDN） |
| 交互流畅度 | 每次操作全量 rerun | 局部更新，无闪烁 |
| 动画与过渡 | CSS hack，效果有限 | 原生 CSS Transitions / Framer Motion |
| 响应式布局 | 受限于 `st.columns` | 完整 CSS Grid / Flexbox |
| 富文本预览 | `st.markdown` 渲染 | 实时 Markdown 编辑器 + 分屏预览 |
| 拖拽排序 | 不支持 | 可实现批量文章拖拽排序 |
| 离线体验 | 断连即不可用 | PWA 缓存，离线可浏览历史 |
| UI 美观度 | 受限于 Streamlit 框架样式 | 完全自定义 Apple HIG 设计系统 |

### 13.4 功能完整保留

**所有 v4.x 功能在 v5 中 100% 保留，无功能裁剪：**

- 37+ 场景生成（16 种语言 × 多场景分类 × 多文风）
- SEO 工具链（评分、Schema、Slug、内链建议）
- GEO 工具链（评分 + 6 项指标 + Prompt 增强）
- AI 检测 + 人性化改写 + 三合一优化
- 双优化（SEO + GEO 联合优化）+ 一键优化到 90+
- 多图库聚合配图（Pixabay + Pexels + Placewise）
- SERP 竞品分析
- 多平台分发（WordPress、Medium、Ghost、LinkedIn 等）
- 外部文章优化检测（Module F）
- 批量生成（多场景并发）
- 完整的评分对比 + 修改说明 + 撤销恢复

### 13.5 v5 新增能力

得益于前端框架的灵活性，v5 可实现以下 Streamlit 无法做到的功能：

| 新能力 | 说明 |
|--------|------|
| Apple HIG 设计系统 | 毛玻璃材质、精细圆角、SF Pro 排版、弹性动效 |
| 实时 Markdown 编辑器 | 生成结果可直接在线编辑，所见即所得 |
| 评分环动画 | SVG 圆环 + 数字计数动画，视觉反馈更直观 |
| 拖拽排序 | 批量文章可拖拽调整顺序 |
| 键盘快捷键 | ⌘+Enter 生成、⌘+S 下载等 |
| 深色/浅色主题切换 | 系统级别主题跟随 + 手动切换 |
| PWA 支持 | 可安装到桌面，离线浏览历史记录 |
| 更好的错误处理 | 前端 Toast 通知 + 请求重试 + 断网提示 |
| 中英文 i18n 切换 | 导航栏一键切换中/英文，localStorage 记忆偏好 |
| 默认 API Key 零配置 | Gemini Key 构建时注入，打开即用，无需手动输入 |
| 60+ 细分订阅场景 | AI 工具/流媒体/开发者/生产力/社交 5 大订阅分类 |
| 11 家 AI 服务商 | 含 Anthropic Claude 原生支持 + Groq/Together/硅基流动/智谱 |
| 冷启动友好提示 | 后端休眠唤醒期间显示 "服务器唤醒中" 提示 |
| 跨页面配置共享 | 工作台配置自动同步到外部文章页面 |

### 13.6 部署变化

| 项目 | v4.x | v5 |
|------|------|-----|
| 前端部署 | Streamlit Cloud（免费） | Cloudflare Pages（免费，无限带宽） |
| 后端部署 | 同 Streamlit Cloud | Railway / Render（免费额度） |
| 域名 | Streamlit 提供子域名 | 可绑定自定义域名 |
| CDN | 无 | Cloudflare 全球 CDN |
| CI/CD | Git push 自动部署 | Git push 自动构建部署（前后端独立） |
| 环境变量 | Streamlit Secrets | 各平台 Dashboard 配置 |

### 13.7 迁移策略

采用**渐进式迁移**，不中断线上服务：

1. **Phase 0** — 完善文档体系（PRD、设计规范、迁移方案、工程规范）← **当前阶段**
2. **Phase 1** — 搭建 FastAPI 后端骨架，将 `app.py` 业务逻辑提取为 API 端点
3. **Phase 2** — 搭建 Next.js 前端骨架，实现创作工作台页面
4. **Phase 3** — 实现 SEO/GEO 分析、外部文章优化、历史记录等剩余页面
5. **Phase 4** — 部署、联调、回归测试
6. **Phase 5** — 切换域名，下线 Streamlit 版本

### 13.8 关联文档

- `DESIGN_SYSTEM.md` — Apple HIG 风格的完整视觉规范
- `MIGRATION_PLAN.md` — 技术迁移详细方案（API 端点、前端路由、部署配置）
- `ENGINEERING_GUIDE.md` — 工程规范（目录结构、命名约定、Git 策略、本地开发）


---

## 14. v5.1 新增功能需求

### 14.1 默认 API Key 嵌入

**需求背景：** 运营同事每次打开工具都需要手动输入 Gemini API Key，增加使用门槛。

**产品要求：**
- 产品默认预填 Gemini API Key，打开即可使用
- 图片服务 Key（Pixabay、Pexels）由后端预配置，无需前端输入
- 用户可在界面覆盖默认值使用自己的 Key
- API Key 通过环境变量注入，源码中不出现明文（GitHub 安全）
- 切换 Provider 时智能管理 Key：切到 Gemini 自动填入默认值，切到其他 Provider 自动清空

### 14.2 字数目标控制

**需求背景：** 前端有字数目标滑块（500-3000），但该值从未传给后端，实际生成字数由 Prompt 中写死的 800-1200 控制。

**产品要求：**
- 前端字数滑块的值传递给后端
- 后端生成 Prompt 使用用户设定的目标字数
- 默认值 1200 字

### 14.3 中英文国际化 (i18n)

**需求背景：** 当前 UI 中英文混杂（英文标题配中文按钮），中文用户看不懂英文标签，英文用户看不懂中文按钮。

**产品要求：**
- UI 支持中文和英文两种语言
- 导航栏右侧提供 "中 / EN" 切换按钮
- 语言偏好存入 localStorage，下次打开自动恢复
- 所有界面文案（按钮、标签、提示语、Tab 名称等）均有中英文翻译
- 翻译覆盖范围：WorkspaceClient（50+ 处）、ExternalClient（20+ 处）、HistoryClient（10+ 处）、Header 导航

### 14.4 外部文章页面配置共享

**需求背景：** 外部文章页面有独立的 API Key / Model / Base URL 输入框，与工作台不联动。切换页面后需重新输入。且 provider 硬编码为 "openai"，导致使用 Gemini Key 时调用失败。

**产品要求：**
- 外部文章页面自动继承工作台的 AI 配置（Provider、Model、API Key、Base URL）
- 使用 localStorage 跨页面共享配置
- 显示紧凑配置条 "AI 配置：Google Gemini / gemini-2.5-flash ✓ [修改]"
- 点击 "修改" 展开完整 Provider 选择器
- 修复 provider 硬编码 "openai" 的 Bug
- 优化/检测按钮不再因无 Key 而禁用

### 14.5 MPChat Logo 与品牌化

**需求背景：** 当前导航栏只有纯文字 "MPChat" + "Content Operating System"，无 Logo，不够专业。

**产品要求：**
- 导航栏显示 MPChat Logo（来自 mp.net 官网）+ 品牌文字
- 更新 favicon
- Logo 高度 32px，与导航栏对齐

### 14.6 冷启动友好提示

**需求背景：** Render 免费层后端休眠 15 分钟后，首次请求需 30-60 秒，用户会看到长时间无响应。

**产品要求：**
- 页面加载时静默预热后端（调用 health 接口）
- 生成/优化按钮点击后超过 5 秒未响应，显示友好提示 "服务器正在唤醒中，首次请求可能需要 30-60 秒..."
- 提示不遮挡内容，收到响应后自动消失
