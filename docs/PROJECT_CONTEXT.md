# MPChat 软文机器人 — 项目架构总结

> 最后更新：2026-03-18 | v5.2 — Phase 1 翻译功能增强：基于源语言动态显示翻译目标

---

## 1. 产品定位

MPChat 软文机器人是一个面向 MPChat 运营团队的 **AI 驱动长文内容生产中心**，核心能力：

- **软文工作台**：基于场景/卖点/文风/关键词参数，一键生成 SEO+GEO 优化的 Markdown 长文
- **多语言翻译**：基于源语言自动推导翻译目标（工作台读取 `form.language`，外部文章页面自动检测），支持简体中文/繁体中文/英文互译，保留完整 Markdown 格式
- **外部文章检测与优化**：对已有博客文章进行 SEO/GEO 评分、AI 检测、多模式优化
- **多平台发布**：生成内容一键分发到 Dev.to、Hashnode、Medium、LinkedIn 等平台
- **历史记录**：本地持久化所有生成记录，支持回溯和复用

---

## 2. 技术栈

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 16.1.6 | React 框架，使用 `output: "export"` 静态导出 |
| React | 19.2.3 | UI 层 |
| TypeScript | ^5 | 类型安全 |
| Tailwind CSS | ^4 | 原子化样式（通过 `@tailwindcss/postcss`） |
| react-markdown + remark-gfm | ^10.1 / ^4.0 | Markdown 渲染 |
| marked | ^17.0 | Markdown → HTML 转换（用于导出） |

**部署**：Cloudflare Pages（静态站点）

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | latest | REST API 框架 |
| Python | 3.11+ | 运行时 |
| uvicorn | latest | ASGI 服务器 |
| OpenAI SDK | latest | LLM 调用（兼容 Gemini/DeepSeek/Groq 等） |
| Anthropic SDK | >=0.40 | Claude 系列模型调用 |
| Pydantic | v2 | 请求/响应模型校验 |
| requests + BeautifulSoup4 | latest | 网页抓取（SERP、知识库） |

**部署**：独立服务器（uvicorn）

### 外部服务

| 服务 | 用途 |
|------|------|
| Google Gemini API | 默认 LLM（gemini-2.5-flash） |
| Pixabay API | 主图片源 |
| Pexels API | 补充图片源 |
| Dev.to API | 文章直发 |
| Hashnode GraphQL API | 文章直发 |
| Google Search | SERP 分析 |

---

## 3. 目录结构

```
MPChat-软文机器人/
│
├── frontend/                          # ===== Next.js 前端 =====
│   ├── app/                           # 页面路由 (App Router)
│   │   ├── layout.tsx                 #   根布局：Geist 字体 + ClientProviders
│   │   ├── page.tsx                   #   / → WorkspaceClient
│   │   ├── globals.css                #   全局样式 + CSS 变量 (~880行)
│   │   ├── external/page.tsx          #   /external → ExternalClient
│   │   └── history/page.tsx           #   /history → HistoryClient
│   │
│   ├── components/                    # React 组件
│   │   ├── WorkspaceClient.tsx        #   软文工作台主组件（含翻译面板）
│   │   ├── ExternalClient.tsx         #   外部文章检测优化（含翻译面板）
│   │   ├── HistoryClient.tsx          #   历史记录列表
│   │   ├── HeaderClient.tsx           #   顶部导航栏
│   │   ├── ScoreRing.tsx              #   环形分数 + 进度条组件
│   │   └── ClientProviders.tsx        #   I18n Provider 包装
│   │
│   ├── lib/                           # 工具库
│   │   ├── api.ts                     #   后端 API 封装 (17 个方法，含 translate/translateExternal)
│   │   ├── types.ts                   #   TypeScript 全局类型定义 (含 TranslateRequest/Response)
│   │   ├── aiConfig.ts                #   localStorage AI 配置持久化
│   │   ├── fallbackConfig.ts          #   后端不可用时的离线降级配置
│   │   ├── history.ts                 #   localStorage 历史记录管理
│   │   └── i18n/                      #   国际化
│   │       ├── index.tsx              #     I18nProvider + useI18n Hook
│   │       ├── zh.json                #     中文文案
│   │       └── en.json                #     英文文案
│   │
│   ├── package.json
│   ├── tsconfig.json                  #   paths: @/* → ./*
│   ├── next.config.ts                 #   output: "export", images: unoptimized
│   └── postcss.config.mjs
│
├── api/                               # ===== FastAPI 后端 =====
│   ├── main.py                        #   应用入口 + CORS + 路由注册
│   ├── services.py                    #   优化 + AI 检测业务逻辑
│   ├── deps.py                        #   依赖注入 (API Key 校验)
│   ├── utils.py                       #   场景/文风/卖点工具函数
│   ├── models/
│   │   ├── requests.py                #   12 个 Pydantic 请求模型（含 TranslateRequest）
│   │   └── responses.py               #   7 个 Pydantic 响应模型（含 TranslateResponse）
│   └── routers/
│       ├── config.py                  #   GET  /config/all|providers|scenarios
│       ├── generate.py                #   POST /generate
│       ├── analyze.py                 #   POST /analyze/seo|geo
│       ├── optimize.py                #   POST /optimize, /detect/ai
│       ├── external.py                #   POST /external/analyze|optimize|translate
│       ├── publish.py                 #   POST /publish/{platform} (8 平台)
│       ├── tools.py                   #   POST /schema, /slug, /links, /serp, /images
│       └── translate.py               #   POST /translate  ← Phase 1 新增
│
├── core/                              # ===== 业务核心层 =====
│   ├── generation.py                  #   LLM 调用 + 文章生成 + JSON 解析 (~409行)
│   ├── translate.py                   #   翻译 Prompt 构建 + translate_article()  ← Phase 1 新增
│   ├── knowledge.py                   #   知识库加载 + 网页抓取
│   ├── providers.py                   #   11 个 AI 服务商配置
│   ├── geo_tools.py                   #   → re-export 根目录 geo_tools
│   ├── seo_tools.py                   #   → re-export 根目录 seo_tools
│   ├── image_client.py                #   → re-export 根目录 image_client
│   ├── publishers.py                  #   → re-export 根目录 publishers
│   ├── scenarios.py                   #   → re-export 根目录 scenarios
│   └── serp_analyzer.py               #   → re-export 根目录 serp_analyzer
│
├── seo_tools.py                       # SEO 工具箱：slug / JSON-LD / 内部链接 / 阅读统计
├── geo_tools.py                       # GEO 工具箱：评分 / FAQ Schema / 优化 Prompt
├── image_client.py                    # 多源图片客户端 (Pixabay/Pexels/Placewise)
├── publishers.py                      # 多平台发布 + 格式化
├── scenarios.py                       # 60+ 场景 / 25+ 卖点 / 7 文风 / 16 语言
├── serp_analyzer.py                   # Google SERP 分析
├── knowledge.txt                      # MPChat 产品知识库 v3.0
├── app.py                             # Streamlit 遗留前端 (~2537行，不再维护)
│
├── .env.example                       # 环境变量模板
├── requirements.txt                   # Python 依赖
├── packages.txt                       # 系统包依赖（空）
│
├── tests/                             # ===== 自动化测试 =====  ← Phase 1 新增
│   ├── test_translate.py              #   core/translate 单元测试 (20 个)
│   ├── test_translate_models.py       #   Pydantic 模型测试 (14 个)
│   └── test_translate_router.py       #   FastAPI 路由集成测试 (13 个)
│
├── .cursorrules                       # Cursor 编码规范
└── docs/
    ├── PRD.md                         # 产品需求文档
    ├── SPEC.md                        # 规格与规范文档
    ├── PROJECT_CONTEXT.md             # ← 本文件
    └── TASK_PLAN.md                   # 功能实施计划
```

---

## 4. 架构分层

```
┌─────────────────────────────────────────────────┐
│              Cloudflare Pages (CDN)              │
│  ┌───────────────────────────────────────────┐   │
│  │       Next.js Static Export (SPA)         │   │
│  │  ┌─────────┐ ┌──────────┐ ┌───────────┐  │   │
│  │  │Workspace│ │ External │ │  History   │  │   │
│  │  │ Client  │ │  Client  │ │  Client    │  │   │
│  │  └────┬────┘ └────┬─────┘ └─────┬─────┘  │   │
│  │       │           │             │         │   │
│  │  ┌────┴───────────┴─────────────┴─────┐   │   │
│  │  │          lib/api.ts (fetch)         │   │   │
│  │  └─────────────────┬──────────────────┘   │   │
│  └────────────────────┼──────────────────────┘   │
└───────────────────────┼──────────────────────────┘
                        │ HTTPS + X-API-Key
┌───────────────────────┼──────────────────────────┐
│              FastAPI Backend Server               │
│  ┌────────────────────┴──────────────────────┐   │
│  │           api/routers/* (7 modules)        │   │
│  │    config │ generate │ analyze │ optimize  │   │
│  │   external │ publish │ tools               │   │
│  └──────┬─────────┬────────────┬─────────────┘   │
│         │         │            │                  │
│  ┌──────┴─────┐ ┌─┴──────┐ ┌──┴──────────┐      │
│  │ services.py│ │utils.py│ │   deps.py    │      │
│  └──────┬─────┘ └────────┘ └─────────────┘      │
│         │                                         │
│  ┌──────┴─────────────────────────────────────┐  │
│  │         core/ (业务核心层)                   │  │
│  │  generation.py │ knowledge.py │ providers.py │  │
│  └──────┬─────────────────────────────────────┘  │
│         │                                         │
│  ┌──────┴─────────────────────────────────────┐  │
│  │     根目录模块 (实际业务实现)                  │  │
│  │  seo_tools │ geo_tools │ image_client       │  │
│  │  publishers │ scenarios │ serp_analyzer      │  │
│  └──────┬──────────────┬──────────────────────┘  │
└─────────┼──────────────┼─────────────────────────┘
          │              │
    ┌─────┴─────┐  ┌─────┴──────────┐
    │ LLM APIs  │  │ External APIs  │
    │ Gemini    │  │ Pixabay/Pexels │
    │ OpenAI    │  │ Dev.to/Hashnode│
    │ Anthropic │  │ Google SERP    │
    │ DeepSeek  │  │                │
    │ 11 家服务商│  │                │
    └───────────┘  └────────────────┘
```

---

## 5. 数据流

### 5.1 文章生成流程

```
用户填写表单 (场景/文风/关键词/卖点)
       │
       ▼
WorkspaceClient.handleGenerate()
       │
       ▼
api.generate(payload)  →  POST /api/v1/generate
       │
       ├─ [可选] fetch_web_knowledge()     → 抓取官网/Medium/Twitter 知识
       ├─ [可选] analyze_serp(keyword)      → Google SERP 竞品分析
       │
       ▼
generate_article()
       │
       ├─ build_system_prompt()  → 知识库 + SEO/GEO 规范 + 场景上下文
       ├─ build_user_prompt()    → 用户参数
       ├─ call_llm()             → Gemini/OpenAI/Anthropic
       ├─ robust_parse()         → JSON 容错解析
       │
       ▼
reading_stats() → SEO 评分
       │
       ├─ [可选] fetch_images_for_article() → Pixabay + Pexels 配图
       │
       ▼
GenerateResponse → 前端渲染 (文章/SEO-GEO/导出/发布/AI检测 5 个 Tab)
```

### 5.2 外部文章优化流程

```
用户粘贴文章 + 输入关键词
       │
       ├─ 「分析」→ POST /external/analyze → reading_stats() + geo_score()
       │              → 返回 SEO/GEO 结构化检查清单
       │
       ├─ 「优化」→ POST /external/optimize → optimize_article_content()
       │              → call_llm(优化 prompt) → parse_opt_result()
       │              → 返回优化文章 + 前后分数对比
       │
       └─ 「AI 检测」→ POST /detect/ai → build_ai_detect_prompt()
                        → call_llm() → 返回 AI 痕迹分析
```

---

## 6. 组件清单

### 前端组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `WorkspaceClient` | `components/WorkspaceClient.tsx` | 软文工作台全流程：配置→生成→预览→SEO/GEO分析→导出→发布→AI检测→**翻译** |
| `ExternalClient` | `components/ExternalClient.tsx` | 外部文章：粘贴→分析(检查清单)→5种优化模式→AI检测→**翻译** |
| `HistoryClient` | `components/HistoryClient.tsx` | 历史记录列表，支持加载到工作台 |
| `HeaderClient` | `components/HeaderClient.tsx` | 顶部导航：Logo + 3 个路由链接 + 中英切换 |
| `ScoreRing` | `components/ScoreRing.tsx` | 环形分数展示组件 (SVG) |
| `BreakdownBar` | `components/ScoreRing.tsx` | 进度条组件 |
| `ClientProviders` | `components/ClientProviders.tsx` | I18n Context Provider 包装 |
| `CheckItem` | `components/ExternalClient.tsx` (内联) | 检查项组件 (pass/fail 图标 + 说明) |

### 前端工具库

| 模块 | 文件 | 导出 |
|------|------|------|
| API 封装 | `lib/api.ts` | `api` 对象 (17 个方法，含 `translate`、`translateExternal`) |
| 类型定义 | `lib/types.ts` | 13 个 interface/type（含 `TranslateRequest`、`TranslateResponse`） |
| AI 配置 | `lib/aiConfig.ts` | `loadAiConfig()`, `saveAiConfig()` |
| 降级配置 | `lib/fallbackConfig.ts` | `FALLBACK_CONFIG` 常量 |
| 历史记录 | `lib/history.ts` | `readHistory()`, `pushHistory()`, `clearHistory()` |
| 国际化 | `lib/i18n/index.tsx` | `I18nProvider`, `useI18n()` |

---

## 7. API 接口完整列表

### 配置

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| GET | `/api/v1/health` | — | `{ ok: true }` |
| GET | `/api/v1/config/all` | — | `ConfigResponse` |
| GET | `/api/v1/config/providers` | — | `Provider[]` |
| GET | `/api/v1/config/scenarios` | — | scenarios + styles + keywords + languages + selling_points |

### 生成

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/v1/generate` | `GenerateRequest` | `GenerateResponse` |

### 分析

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/v1/analyze/seo` | `ArticleAnalyzeRequest` | `AnalyzeResponse` |
| POST | `/api/v1/analyze/geo` | `ArticleAnalyzeRequest` | `AnalyzeResponse` |
| POST | `/api/v1/external/analyze` | `ExternalAnalyzeRequest` | `{ seo, geo }` |

### 优化

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/v1/optimize` | `OptimizeRequest` | `OptimizeResponse` |
| POST | `/api/v1/external/optimize` | `OptimizeRequest` | `OptimizeResponse` |
| POST | `/api/v1/detect/ai` | `AiDetectRequest` | `{ result: AiDetectResult }` |

### 翻译（Phase 1 新增）

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/v1/translate` | `TranslateRequest` | `TranslateResponse` |
| POST | `/api/v1/external/translate` | `TranslateRequest` | `TranslateResponse` |

### 发布

| 方法 | 路径 | 模式 | 说明 |
|------|------|------|------|
| POST | `/api/v1/publish/devto` | API 直发 | 需要 Dev.to API Key |
| POST | `/api/v1/publish/hashnode` | API 直发 | 需要 Token + Publication ID |
| POST | `/api/v1/publish/medium` | 格式预览 | 返回 Markdown 预览文本 |
| POST | `/api/v1/publish/linkedin` | 格式预览 | 纯文本，3000 字限制 |
| POST | `/api/v1/publish/twitter` | 格式预览 | 分割为推文线程 |
| POST | `/api/v1/publish/zhihu` | 格式预览 | 知乎 Markdown 格式 |
| POST | `/api/v1/publish/wechat` | 格式预览 | 微信纯文本 |
| POST | `/api/v1/publish/crypto` | 格式预览 | 加密博客 frontmatter |

### 工具

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/v1/schema` | `SchemaRequest` | Article + FAQ JSON-LD |
| POST | `/api/v1/slug` | `SlugRequest` | `{ slug }` |
| POST | `/api/v1/links` | `LinksRequest` | `{ links }` |
| POST | `/api/v1/serp/analyze` | `SerpAnalyzeRequest` | SERP 分析结果 |
| POST | `/api/v1/images/search` | `ImageSearchRequest` | `{ images }` |

---

## 8. 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `OPENAI_API_KEY` | 是 | 默认 LLM API Key（目前使用 Gemini） |
| `OPENAI_BASE_URL` | 是 | LLM API Base URL |
| `OPENAI_MODEL` | 否 | 默认模型名 |
| `PIXABAY_API_KEY` | 否 | Pixabay 图片搜索 |
| `PEXELS_API_KEY` | 否 | Pexels 图片搜索 |
| `DEVTO_API_KEY` | 否 | Dev.to 发布 |
| `HASHNODE_TOKEN` | 否 | Hashnode 发布 |
| `HASHNODE_PUB_ID` | 否 | Hashnode Publication ID |
| `MPCHAT_API_KEY` | 否 | API 接口保护 |
| `CORS_ALLOW_ORIGINS` | 否 | 跨域允许来源 |
| `NEXT_PUBLIC_API_URL` | 是 | 前端连接后端的 URL |
| `NEXT_PUBLIC_API_KEY` | 否 | 前端 API Key |
| `NEXT_PUBLIC_DEFAULT_GEMINI_KEY` | 否 | 前端默认 Gemini Key（不提交 Git） |

---

## 9. 状态管理

前端没有使用 Redux/Zustand 等状态管理库，采用以下策略：

- **组件级状态**：`useState` 管理表单数据、生成结果、loading 状态
- **持久化**：`localStorage` 存储 AI 配置 (`mpchat-ai-config`) 和历史记录 (`mpchat-history`)
- **跨页面通信**：历史记录加载到工作台通过 `localStorage` 的 `mpchat-load-workspace` key
- **国际化**：React Context (`I18nProvider`) + `localStorage` (`mpchat-locale`)

---

## 10. 已知架构特点

1. **core/ 目录是桥接层**：`core/*.py` 大多是 `from xxx import *` 的 re-export，实际业务逻辑在根目录模块中。这是因为项目从 Streamlit 单文件架构迁移而来。
2. **LLM 调用统一入口**：`core/generation.py` 中的 `call_llm()` 函数统一处理 Anthropic (独立 SDK) 和 OpenAI 兼容 API (其余 10 家服务商) 的差异。
3. **JSON 容错解析**：`robust_parse()` 实现了多层容错（标准 JSON → 修复尾逗号 → 换行符转义 → 正则提取字段），应对不同 LLM 输出格式差异。
4. **SEO/GEO 评分是本地计算**：`reading_stats()` 和 `geo_score()` 是纯 Python 正则匹配，不依赖外部 API，执行速度快。
5. **前端静态导出**：`output: "export"` 意味着无 SSR，所有组件必须标记 `"use client"`，API 调用在客户端完成。
