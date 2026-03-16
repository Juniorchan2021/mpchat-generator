# MPChat v5 工程规范

> 本文档定义 MPChat v5 前后端分离项目的工程规范，包括目录结构、编码约定、环境变量、Git 策略、部署流程和本地开发指南。

---

## 目录

1. [项目目录结构](#1-项目目录结构)
2. [后端规范（FastAPI）](#2-后端规范fastapi)
3. [前端规范（Next.js）](#3-前端规范nextjs)
4. [环境变量清单](#4-环境变量清单)
5. [Git 分支策略](#5-git-分支策略)
6. [部署流程](#6-部署流程)
7. [本地开发](#7-本地开发)
8. [测试策略](#8-测试策略)

---

## 1. 项目目录结构

```
MPChat-软文机器人/
│
├── api/                            # ── FastAPI 后端 ──
│   ├── main.py                     # 应用入口：app 实例、CORS、全局异常处理
│   ├── routers/                    # 子路由（按业务模块拆分）
│   │   ├── __init__.py
│   │   ├── config.py               # GET /api/v1/config/*
│   │   ├── generate.py             # POST /api/v1/generate
│   │   ├── analyze.py              # POST /api/v1/analyze/seo, /api/v1/analyze/geo
│   │   ├── optimize.py             # POST /api/v1/optimize
│   │   ├── external.py             # POST /api/v1/external/*
│   │   ├── publish.py              # POST /api/v1/publish/*
│   │   └── tools.py                # POST /api/v1/schema, /api/v1/slug, /api/v1/links
│   ├── models/                     # Pydantic 数据模型
│   │   ├── __init__.py
│   │   ├── requests.py             # 请求体（*Request 类）
│   │   └── responses.py            # 响应体（*Response 类）
│   ├── deps.py                     # 公共依赖注入（如 API Key 校验）
│   └── utils.py                    # 后端工具函数（JSON 解析兜底等）
│
├── frontend/                       # ── Next.js 前端 ──
│   ├── app/                        # App Router 页面
│   │   ├── layout.tsx              # 根布局（侧边栏 + 顶栏）
│   │   ├── page.tsx                # / — 创作工作台
│   │   ├── external/
│   │   │   └── page.tsx            # /external — 外部文章优化
│   │   └── history/
│   │       └── page.tsx            # /history — 生成历史
│   ├── components/
│   │   ├── ui/                     # 通用 UI 组件
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── SegmentedControl.tsx
│   │   │   ├── ScoreRing.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Expander.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── index.ts            # 统一导出
│   │   └── features/               # 业务组件
│   │       ├── ConfigBar.tsx        # 配置条
│   │       ├── ArticlePreview.tsx   # 文章预览
│   │       ├── SeoPanel.tsx         # SEO 分析面板
│   │       ├── GeoPanel.tsx         # GEO 分析面板
│   │       ├── PublishPanel.tsx     # 分发面板
│   │       ├── ExternalAnalyzer.tsx # 外部文章分析
│   │       ├── HistoryList.tsx      # 历史记录列表
│   │       └── Sidebar.tsx          # 侧边栏
│   ├── lib/
│   │   ├── api.ts                  # 后端 API 调用封装
│   │   ├── constants.ts            # 前端常量
│   │   └── utils.ts                # 前端工具函数
│   ├── hooks/
│   │   ├── useGenerate.ts          # 生成文章 hook
│   │   ├── useAnalyze.ts           # 分析 hook
│   │   └── useHistory.ts           # 历史记录 hook
│   ├── styles/
│   │   └── globals.css             # Tailwind 指令 + CSS 变量（来自 DESIGN_SYSTEM.md §8）
│   ├── public/
│   │   └── favicon.ico
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── core/                           # ── 共享 Python 模块（包）──
│   ├── __init__.py
│   ├── scenarios.py                # 场景/卖点/文风/关键词/语言数据
│   ├── image_client.py             # 多图库聚合
│   ├── seo_tools.py                # SEO 工具
│   ├── geo_tools.py                # GEO 工具
│   ├── publishers.py               # 多平台分发
│   ├── serp_analyzer.py            # SERP 分析
│   └── knowledge.txt               # 产品知识库
│
├── tests/                          # ── 测试 ──
│   ├── conftest.py                 # pytest fixtures（mock LLM、mock 图片 API 等）
│   ├── test_generate.py            # 生成 API 测试
│   ├── test_analyze.py             # SEO/GEO 分析测试
│   ├── test_optimize.py            # 优化 API 测试
│   ├── test_publish.py             # 分发 API 测试
│   └── test_core.py                # core/ 模块单元测试
│
├── app.py                          # v4.x Streamlit 入口（迁移完成后归档）
├── requirements.txt                # 后端 Python 依赖
├── .env.example                    # 环境变量模板
├── .gitignore
├── PRD.md
├── DESIGN_SYSTEM.md
├── MIGRATION_PLAN.md
└── ENGINEERING_GUIDE.md            # 本文档
```

---

## 2. 后端规范（FastAPI）

### 2.1 路由组织

每个 `routers/*.py` 文件创建一个 `APIRouter` 实例，在 `main.py` 中统一注册：

```python
# api/routers/generate.py
from fastapi import APIRouter
from core.scenarios import SCENARIOS, LANGUAGES, STYLES
from core.image_client import fetch_images_for_article
from core.seo_tools import reading_stats
from core.geo_tools import geo_score

router = APIRouter(prefix="/api/v1", tags=["generate"])

@router.post("/generate")
async def generate_article(req: GenerateRequest) -> GenerateResponse:
    ...
```

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import config, generate, analyze, optimize, external, publish, tools

app = FastAPI(title="MPChat API", version="5.0.0", docs_url="/api/v1/docs", openapi_url="/api/v1/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mpchat.pages.dev", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in [config.router, generate.router, analyze.router,
          optimize.router, external.router, publish.router, tools.router]:
    app.include_router(r)
```

### 2.2 Pydantic 模型命名

| 类型 | 命名规则 | 示例 |
|------|----------|------|
| 请求体 | `{Action}Request` | `GenerateRequest`, `SeoAnalyzeRequest` |
| 响应体 | `{Action}Response` | `GenerateResponse`, `SeoAnalyzeResponse` |
| 嵌套模型 | `{Entity}` | `ImageItem`, `KeywordDensity`, `ScoreBreakdown` |

所有模型放在 `api/models/` 中，按请求/响应分文件。

### 2.3 错误处理

统一使用 `HTTPException`，自定义错误响应格式：

```python
from fastapi import HTTPException

# 参数校验失败
raise HTTPException(status_code=422, detail="keywords 不能为空")

# LLM 调用失败
raise HTTPException(status_code=502, detail="LLM 服务暂时不可用，请稍后重试")

# 第三方 API 失败
raise HTTPException(status_code=503, detail="Pixabay API 请求失败")
```

错误码约定：

| 状态码 | 场景 |
|--------|------|
| 400 | 请求格式错误 |
| 422 | 参数校验失败（Pydantic 自动返回） |
| 502 | LLM / 第三方 API 调用失败 |
| 503 | 服务暂时不可用 |
| 504 | 请求超时（LLM 生成超时） |

### 2.4 日志

使用 Python `logging` 标准库，格式统一：

```python
import logging
logger = logging.getLogger("mpchat")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
```

关键操作记录 INFO 级别日志：
- API 请求进入（端点、参数摘要）
- LLM 调用开始/完成（模型、耗时）
- 图片搜索结果数
- 错误详情（ERROR 级别）

---

## 3. 前端规范（Next.js）

### 3.1 目录约定

| 目录 | 内容 | 说明 |
|------|------|------|
| `app/` | 页面路由 | 每个路由一个 `page.tsx`，布局用 `layout.tsx` |
| `components/ui/` | 通用 UI 组件 | 与业务无关，可独立复用 |
| `components/features/` | 业务组件 | 与 MPChat 功能强耦合 |
| `lib/` | 工具库 | API 调用、常量、纯函数 |
| `hooks/` | 自定义 Hooks | 封装 API 调用 + 状态管理 |
| `styles/` | 全局样式 | CSS 变量 + Tailwind 指令 |

### 3.2 命名规范

| 类别 | 规则 | 示例 |
|------|------|------|
| 组件文件 | PascalCase.tsx | `ScoreRing.tsx`, `ConfigBar.tsx` |
| 页面文件 | 小写 `page.tsx` | `app/external/page.tsx` |
| Hook 文件 | camelCase.ts | `useGenerate.ts`, `useHistory.ts` |
| 工具函数 | camelCase | `formatScore()`, `parseMarkdown()` |
| CSS 类名 | kebab-case / Tailwind | `score-ring`, `btn-primary` |
| 常量 | UPPER_SNAKE_CASE | `API_BASE_URL`, `MAX_HISTORY_ITEMS` |
| TypeScript 接口 | PascalCase + I 前缀可选 | `GenerateRequest`, `ArticleData` |

### 3.3 状态管理

- **服务端数据**：使用 `SWR` 或 `React Query`（TanStack Query）管理 API 请求、缓存和重新验证
- **客户端状态**：使用 React `useState` / `useReducer`，无需引入 Redux
- **持久化**：生成历史存 `localStorage`，最多保留 50 条

### 3.4 API 调用封装

所有后端请求通过 `lib/api.ts` 统一发出：

```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const API_KEY = process.env.NEXT_PUBLIC_API_KEY;
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
    },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "请求失败");
  }
  return res.json();
}

export const api = {
  generate: (data: GenerateRequest) =>
    request<GenerateResponse>("/api/v1/generate", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  analyzeSeo: (data: SeoRequest) =>
    request<SeoResponse>("/api/v1/analyze/seo", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  // ... 其余端点
};
```

### 3.5 组件结构

每个组件遵循以下结构（无需逐行注释）：

```typescript
// components/ui/ScoreRing.tsx
"use client";

interface ScoreRingProps {
  score: number;
  size?: "sm" | "md" | "lg";
  label?: string;
}

export function ScoreRing({ score, size = "md", label }: ScoreRingProps) {
  // component logic
  return (/* JSX */);
}
```

---

## 4. 环境变量清单

### 4.1 后端环境变量

| 变量名 | 用途 | 必填 | 默认值 |
|--------|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | 否（用户可自带） | - |
| `OPENAI_BASE_URL` | OpenAI API 基地址（兼容第三方） | 否 | `https://api.openai.com/v1` |
| `GOOGLE_API_KEY` | Google Gemini API 密钥 | 否 | - |
| `PIXABAY_API_KEY` | Pixabay 图片搜索 | 是 | - |
| `PEXELS_API_KEY` | Pexels 图片搜索 | 否 | - |
| `SERP_API_KEY` | SERP API（竞品分析） | 否 | - |
| `DEVTO_API_KEY` | Dev.to 发布 | 否 | - |
| `HASHNODE_TOKEN` | Hashnode 发布 | 否 | - |
| `HASHNODE_PUBLICATION_ID` | Hashnode 出版物 ID | 否 | - |
| `MEDIUM_TOKEN` | Medium 发布 | 否 | - |
| `GHOST_URL` | Ghost 博客 URL | 否 | - |
| `GHOST_ADMIN_KEY` | Ghost Admin API Key | 否 | - |
| `WP_URL` | WordPress 站点 URL | 否 | - |
| `WP_USER` | WordPress 用户名 | 否 | - |
| `WP_APP_PASSWORD` | WordPress 应用密码 | 否 | - |
| `MPCHAT_API_KEY` | API 认证密钥（见 MIGRATION_PLAN §7.2） | 否（未设则跳过认证） | - |
| `PORT` | 后端监听端口 | 否 | `8000` |
| `LOG_LEVEL` | 日志级别 | 否 | `INFO` |

### 4.2 前端环境变量

| 变量名 | 用途 | 必填 | 默认值 |
|--------|------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端 API 基地址 | 是 | `http://localhost:8000` |
| `NEXT_PUBLIC_API_KEY` | 后端认证密钥（对应后端 `MPCHAT_API_KEY`） | 否（本地开发可不配） | - |
| `NEXT_PUBLIC_DEFAULT_GEMINI_KEY` | 默认 Gemini API Key（v5.1 新增） | 推荐 | - |
| `NEXT_PUBLIC_DEFAULT_PEXELS_KEY` | 默认 Pexels Key（前端展示用） | 否 | - |
| `NEXT_PUBLIC_DEFAULT_PIXABAY_KEY` | 默认 Pixabay Key（前端展示用） | 否 | - |

> `NEXT_PUBLIC_` 前缀的变量会被打包到客户端代码中。虽然 Key 会出现在 JS 包中，但由于前端部署在 Cloudflare Pages（私有 URL），且本工具仅供内部团队使用，风险可控。源码仓库中不出现明文，通过 Cloudflare Pages Environment Variables 注入。

---

## 5. Git 分支策略

```
main ─────────────────────────────────── 生产分支（Cloudflare Pages 自动部署）
  │
  ├── dev ────────────────────────────── 开发集成分支
  │     │
  │     ├── feature/api-generate ────── 功能分支：后端生成 API
  │     ├── feature/frontend-workspace  功能分支：前端创作工作台
  │     ├── feature/seo-panel ───────── 功能分支：SEO 分析面板
  │     └── fix/cors-config ─────────── 修复分支
  │
  └── (release/v5.0) ────────────────── 可选：预发布分支
```

### 5.1 分支规则

| 分支 | 保护 | 合并方式 | 说明 |
|------|------|----------|------|
| `main` | 受保护，不可直接 push | 仅通过 PR 合并 | 每次合并触发 Cloudflare Pages 构建 |
| `dev` | 推荐 PR 合并 | Squash merge | 日常开发集成 |
| `feature/*` | 无保护 | 合并到 `dev` 后删除 | 单个功能/任务 |
| `fix/*` | 无保护 | 合并到 `dev` 后删除 | Bug 修复 |

### 5.2 Commit 规范

采用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <description>

feat(api): add /api/generate endpoint with image support
fix(frontend): correct score ring animation timing
docs: update MIGRATION_PLAN with API examples
style(ui): adjust card border radius to match design system
refactor(api): extract LLM call logic into shared util
```

| type | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `style` | UI/样式调整 |
| `refactor` | 重构（不改功能） |
| `test` | 测试 |
| `chore` | 构建/工具/依赖 |

---

## 6. 部署流程

### 6.1 后端部署（Railway / Render）

#### Railway

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 初始化项目（首次）
railway init

# 部署
railway up
```

**Railway 配置：**
- **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- **Root Directory**: `/`（项目根目录）
- **Environment Variables**: 在 Railway Dashboard 中配置（见 §4.1）
- **Region**: 选择 US West 或最近的区域

#### Render

**render.yaml:**

```yaml
services:
  - type: web
    name: mpchat-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
      - key: PORT
        value: "8000"
```

### 6.2 前端部署（Cloudflare Pages）

#### 方式 1：Git 集成（推荐）

1. 在 Cloudflare Dashboard → Pages → Create a project
2. 连接 Git 仓库
3. 配置构建：
   - **Framework preset**: Next.js
   - **Build command**: `cd frontend && npm ci && npm run build`
   - **Build output directory**: `frontend/.next`（使用 `@cloudflare/next-on-pages`）或 `frontend/out`（静态导出）
4. 添加环境变量：`NEXT_PUBLIC_API_URL = https://mpchat-api.railway.app`
5. 部署

#### 方式 2：CLI 部署（绕过构建次数限制）

```bash
# 安装 Wrangler
npm install -g wrangler

# 本地构建
cd frontend
npm ci && npm run build

# 部署
wrangler pages deploy out --project-name=mpchat
```

### 6.3 部署检查清单

- [ ] 后端 `/api/v1/config/providers` 返回 200
- [ ] 后端 CORS 包含前端域名
- [ ] 前端 `NEXT_PUBLIC_API_URL` 指向正确的后端地址
- [ ] 前端首页可正常加载
- [ ] 生成文章流程端到端通过
- [ ] SEO/GEO 分析返回正确评分
- [ ] 多平台分发至少 1 个平台测试通过

---

## 7. 本地开发

### 7.1 环境要求

| 工具 | 版本 | 安装 |
|------|------|------|
| Python | 3.11+ | `brew install python@3.11` 或 pyenv |
| Node.js | 18+ | `brew install node` 或 nvm |
| npm | 9+ | 随 Node.js 安装 |
| Git | 2.40+ | `brew install git` |

### 7.2 后端启动

```bash
# 1. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 4. 启动开发服务器
uvicorn api.main:app --reload --port 8000
```

后端运行在 `http://localhost:8000`，自动文档在 `http://localhost:8000/api/v1/docs`（Swagger UI）。

### 7.3 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 配置环境变量
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# 4. 启动开发服务器
npm run dev
```

前端运行在 `http://localhost:3000`，热更新（HMR）已自动启用。

### 7.4 联调配置

开发时前后端分别运行：

```
浏览器 → http://localhost:3000 (Next.js)
                    │
                    ▼ fetch
         http://localhost:8000 (FastAPI)
```

- 后端 CORS 已配置允许 `http://localhost:3000`
- 前端 `.env.local` 中 `NEXT_PUBLIC_API_URL=http://localhost:8000`
- 修改后端代码 → uvicorn `--reload` 自动重启
- 修改前端代码 → Next.js HMR 自动刷新

### 7.5 常用命令速查

| 操作 | 命令 |
|------|------|
| 启动后端 | `uvicorn api.main:app --reload --port 8000` |
| 启动前端 | `cd frontend && npm run dev` |
| 后端测试 | `pytest tests/ -v` |
| 前端构建 | `cd frontend && npm run build` |
| 前端 lint | `cd frontend && npm run lint` |
| 类型检查 | `cd frontend && npx tsc --noEmit` |
| 格式化 | `cd frontend && npx prettier --write .` |
| 后端文档 | 浏览器打开 `http://localhost:8000/api/v1/docs` |

---

## 8. 测试策略

### 8.1 测试工具

| 层级 | 工具 | 说明 |
|------|------|------|
| 后端单元测试 | `pytest` + `pytest-asyncio` | 测试 core/ 模块的纯函数 |
| 后端 API 测试 | `httpx` + `pytest` | 使用 FastAPI TestClient 测试端点 |
| 前端单元测试 | `vitest` + `@testing-library/react` | 测试组件和 hooks |
| 前端 E2E 测试 | `Playwright`（可选） | 端到端流程测试 |

### 8.2 后端测试规范

**目录结构：**

```
tests/
├── conftest.py          # 共享 fixtures
├── test_generate.py     # /api/v1/generate 端点
├── test_analyze.py      # /api/v1/analyze/* 端点
├── test_optimize.py     # /api/v1/optimize 端点
├── test_publish.py      # /api/v1/publish/* 端点
└── test_core.py         # core/ 模块纯函数
```

**conftest.py 核心 fixtures：**

```python
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_llm_response(monkeypatch):
    """Mock LLM API 调用，避免消耗真实 API 额度"""
    async def mock_call(*args, **kwargs):
        return {
            "article": "# Mock Article\n\nMock content...",
            "title": "Mock Title",
            "faq_pairs": []
        }
    monkeypatch.setattr("core.llm_client.call_llm", mock_call)

@pytest.fixture
def mock_image_api(monkeypatch):
    """Mock 图片 API，避免真实网络请求"""
    async def mock_search(*args, **kwargs):
        return [{"url": "https://example.com/img.jpg", "alt": "test", "source": "mock"}]
    monkeypatch.setattr("core.image_client.search_pixabay", mock_search)
```

**测试示例：**

```python
# tests/test_generate.py
def test_generate_requires_api_key(client):
    res = client.post("/api/v1/generate", json={"language": "中文"})
    assert res.status_code == 422

def test_generate_success(client, mock_llm_response, mock_image_api):
    res = client.post("/api/v1/generate", json={
        "provider": "openai",
        "model": "gpt-4o",
        "api_key": "test-key",
        "language": "中文",
        "category": "数字货币",
        "scenario": "比特币入门指南",
        "style": "专业严谨",
        "keywords": "比特币"
    })
    assert res.status_code == 200
    data = res.json()
    assert "article" in data
    assert "title" in data

# tests/test_core.py
from core.seo_tools import reading_stats

def test_reading_stats_basic():
    stats = reading_stats("# Title\n\n## Section 1\n\nSome text here. " * 100)
    assert stats["word_count"] > 0
    assert stats["h2_count"] >= 1
    assert stats["reading_time_min"] > 0
```

### 8.3 前端测试规范

**组件测试示例：**

```typescript
// components/ui/__tests__/ScoreRing.test.tsx
import { render, screen } from "@testing-library/react";
import { ScoreRing } from "../ScoreRing";

test("renders score value", () => {
  render(<ScoreRing score={85} />);
  expect(screen.getByText("85")).toBeInTheDocument();
});

test("applies green color for score >= 90", () => {
  const { container } = render(<ScoreRing score={95} />);
  const circle = container.querySelector(".score-ring__circle");
  expect(circle).toHaveStyle({ stroke: "var(--accent-green)" });
});
```

**API Hook 测试：**

```typescript
// hooks/__tests__/useGenerate.test.ts
import { renderHook, waitFor } from "@testing-library/react";
import { useGenerate } from "../useGenerate";

test("returns loading state during generation", async () => {
  const { result } = renderHook(() => useGenerate());
  result.current.generate({ /* params */ });
  expect(result.current.isLoading).toBe(true);
});
```

### 8.4 测试命令

| 操作 | 命令 |
|------|------|
| 后端全量测试 | `pytest tests/ -v` |
| 后端单文件 | `pytest tests/test_generate.py -v` |
| 后端覆盖率 | `pytest tests/ --cov=api --cov=core --cov-report=html` |
| 前端全量测试 | `cd frontend && npm test` |
| 前端覆盖率 | `cd frontend && npm test -- --coverage` |
| 前端 E2E | `cd frontend && npx playwright test` |

### 8.5 CI 集成建议

在 GitHub Actions 中，每次 PR 自动运行：

```yaml
# .github/workflows/test.yml
name: Test
on: [pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt && pip install pytest pytest-asyncio httpx
      - run: pytest tests/ -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "18" }
      - run: cd frontend && npm ci && npm test
```


---

## 9. Anthropic Claude 适配层（v5.1 新增）

### 9.1 问题

后端统一使用 `openai` Python SDK 调用 LLM。Anthropic (Claude) 的 API 使用不同的请求格式（`x-api-key` header、`anthropic-version` header、不同的 `messages` 结构），无法直接使用 OpenAI SDK。

### 9.2 双通道方案

Claude 同时支持两种调用路径：

**路径 A — OpenRouter 中转（已支持）**：用户选择 OpenRouter 作为 Provider，使用 Claude 模型名（如 `anthropic/claude-sonnet-4`），无需额外适配。

**路径 B — 原生 Anthropic SDK（v5.1 新增）**：用户选择 Anthropic 作为 Provider，使用 `anthropic` Python SDK 直连。

### 9.3 实现

在 `core/generation.py` 中添加统一调用入口：

```python
def call_llm(provider: str, api_key: str, base_url: str,
             model: str, messages: list, max_tokens: int = 16384) -> str:
    if provider == "anthropic":
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        # Anthropic 要求 system 和 user 分开
        system_msg = ""
        user_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                user_msgs.append(m)
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_msg,
            messages=user_msgs,
        )
        return resp.content[0].text
    else:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url or None)
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return resp.choices[0].message.content
```

### 9.4 影响范围

所有直接调用 `client.chat.completions.create()` 的位置需改为调用 `call_llm()`。

### 9.5 依赖

`requirements.txt` 新增：`anthropic>=0.40.0`

---

## 10. 国际化 (i18n) 架构（v5.1 新增）

### 10.1 技术选型

- **方案**：React Context + JSON 翻译文件
- **原因**：`output: "export"` 静态导出不支持 Next.js i18n 中间件
- **不引入第三方库**（如 react-i18next），保持轻量

### 10.2 文件结构

```
frontend/lib/i18n/
├── index.tsx   # I18nProvider + useI18n hook
├── zh.json     # 中文翻译（80+ key）
└── en.json     # 英文翻译（80+ key）
```

### 10.3 核心实现

```typescript
// frontend/lib/i18n/index.tsx
"use client";
import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import zh from "./zh.json";
import en from "./en.json";

type Locale = "zh" | "en";
const dictionaries = { zh, en } as const;

interface I18nCtx {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nCtx>({
  locale: "zh", setLocale: () => {}, t: (k) => k,
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("mpchat-locale") as Locale) || "zh";
    }
    return "zh";
  });

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    localStorage.setItem("mpchat-locale", l);
  }, []);

  const t = useCallback(
    (key: string) => (dictionaries[locale] as Record<string, string>)[key] ?? key,
    [locale]
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export const useI18n = () => useContext(I18nContext);
```

### 10.4 翻译 Key 命名规则

`{area}.{element}` 格式：

| 前缀 | 含义 | 示例 |
|------|------|------|
| `nav.*` | 导航栏 | `nav.workspace`, `nav.external`, `nav.history` |
| `btn.*` | 按钮 | `btn.generate`, `btn.analyze`, `btn.copy` |
| `tab.*` | Tab 标签 | `tab.article`, `tab.seoGeo`, `tab.export` |
| `form.*` | 表单标签 | `form.provider`, `form.model`, `form.keywords` |
| `msg.*` | 提示消息 | `msg.serverWarmup`, `msg.generateSuccess` |
| `empty.*` | 空状态 | `empty.history`, `empty.article` |
| `err.*` | 错误 | `err.requestFailed`, `err.invalidKey` |

### 10.5 使用方式

```typescript
const { t, locale, setLocale } = useI18n();

// 翻译文案
<button>{t("btn.generate")}</button>

// 语言切换
<button onClick={() => setLocale(locale === "zh" ? "en" : "zh")}>
  {locale === "zh" ? "EN" : "中"}
</button>
```

---

## 11. localStorage 约定（v5.1 新增）

| Key | 用途 | 格式 | 清理策略 |
|-----|------|------|----------|
| `mpchat-ai-config` | AI 配置（跨页面共享） | `{ provider, model, api_key, base_url }` | 不自动清理 |
| `mpchat-locale` | 语言偏好 | `"zh"` 或 `"en"` | 不自动清理 |
| `mpchat-history` | 生成历史记录 | 数组，最多 50 条 | 超过 50 条时 FIFO 淘汰 |
| `mpchat-load-workspace` | 从历史加载到工作台 | 临时数据 | 读取后立即删除 |

### aiConfig.ts 工具模块

```typescript
// frontend/lib/aiConfig.ts
const STORAGE_KEY = "mpchat-ai-config";

export interface AiConfig {
  provider: string;
  model: string;
  api_key: string;
  base_url: string;
}

export function loadAiConfig(): AiConfig | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(STORAGE_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function saveAiConfig(config: AiConfig): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
}
```

---

## 12. 字数目标全链路（v5.1 新增）

前端到后端到 Prompt 的完整数据流：

```
用户拖动滑块 (wordCountTarget: 1500)
       │
WorkspaceClient 调用 api.generate({ ...form, word_count_target: 1500 })
       │
POST /api/v1/generate  →  req.word_count_target = 1500
       │
generate_article(word_count_target=1500)
       │
Prompt: "文章总字数控制在 1500 字左右"
```

**涉及文件：**

| 文件 | 改动 |
|------|------|
| `frontend/lib/types.ts` | `GenerateRequest` 增加 `word_count_target?: number` |
| `frontend/components/WorkspaceClient.tsx` | generate 调用时传入 `word_count_target` |
| `api/models/requests.py` | `GenerateRequest` 增加 `word_count_target: int = 1200` |
| `api/routers/generate.py` | 将 `req.word_count_target` 传入 `generate_article()` |
| `core/generation.py` | Prompt 中使用 `f"文章总字数控制在 {word_count_target} 字左右"` |
