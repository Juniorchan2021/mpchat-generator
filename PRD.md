# MPChat 智能软文生成器 — 产品设计说明文档

**版本：v4.0.1**
**当前版本：v4.0.1 (已上线)**
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

### 3.6 配图系统（3 级图源策略）

采用 3 级 fallback 架构，确保始终有图可用：

- **Tier 1 — Pixabay（主图源）**：REST API 搜索，返回高分辨率图片 + 摄影师元数据，100 次/分钟，需 API Key
- **Tier 2 — Pexels（补充图源）**：REST API 搜索，200 次/小时免费额度，需 API Key（可选）
- **Tier 3 — Placewise CDN（兜底）**：URL-based 语义图片服务（`img.placewise.io/800x600-query`），无需 API Key，当 Pixabay + Pexels 均无结果时自动启用
- 自动在文章 H2 标题后插入配图（st.image() 渲染）
- AI 配图提示词（Midjourney / DALL-E）同时输出

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
Tab 3: 阅读统计 + SEO 评分（0-100）+ 一键 SEO 优化
Tab 4: GEO 评分（0-100）+ 一键 GEO 优化
Tab 5: AI 内容检测 + 一键人性化改写

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

### 9.2 SEO/GEO 优化按钮无响应（v4.0 → v4.0.1 修复）

**问题描述：** 点击「一键 SEO 优化到 90+」或「一键 GEO 优化到 90+」后，加载动画出现但页面无变化。

**根因分析：**
- 按钮点击后 LLM 返回优化文章，代码调用 `st.rerun()` 刷新页面
- `st.rerun()` 在 `st.spinner()` + `st.tabs()` 嵌套上下文内调用时行为异常
- 页面重新执行后，Tab 重置到第一个（Schema），用户看不到优化结果
- 部分情况下 `st.rerun()` 在嵌套上下文中被 Streamlit 静默忽略

**修复方案：** 延迟 rerun 模式
1. 优化完成后，结果写入 `st.session_state`，设置 `_pending_rerun = True`
2. 显示 `st.success()` 反馈消息
3. 在输出区域顶部检测 `_pending_rerun` flag，在安全上下文中执行 `st.rerun()`
4. 同样模式应用于 SEO 优化、GEO 优化、人性化改写三个按钮

**影响文件：** `app.py`（Module D 三个优化按钮 + 输出区域顶部 rerun 检查）

### 9.3 API Key 安全存储（v4.0 → v4.0.1 修复）

**问题描述：** Gemini API Key 硬编码在源码中，推送到 GitHub 后被 Google 自动扫描吊销。

**修复方案：**
1. 从代码中移除所有明文 API Key
2. 使用 `st.secrets["GEMINI_API_KEY"]` 从 Streamlit Cloud Secrets 安全读取
3. 回退到 `os.getenv("OPENAI_API_KEY")` 支持本地开发
4. 用户可在侧边栏手动输入覆盖
