# MPChat 智能软文生成器 — 产品设计说明文档

**版本：v4.1**
**当前版本：v4.1 (已上线)**
**最后更新：2026-03-11**
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

```
MPChat-软文机器人/
├── app.py              # 主应用
├── scenarios.py         # 场景/卖点/文风/关键词/语言数据
├── image_client.py      # 多图库聚合（Placewise + Pixabay）
├── seo_tools.py         # SEO 工具
├── geo_tools.py         # GEO 评分 + Schema + Prompt 增强
├── publishers.py        # 多平台发布格式化 + API 集成
├── serp_analyzer.py     # SERP 分析器
├── knowledge.txt        # MPChat 产品知识库
├── requirements.txt     # Python 依赖
├── packages.txt         # 系统级依赖
├── .env.example         # 环境变量示例
├── PRD.md               # 本产品设计文档
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
