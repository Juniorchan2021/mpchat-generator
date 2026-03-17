# MPChat 软文机器人 — 规格与规范文档

> 版本：v5.2 | 最后更新：2026-03-18

---

## 1. API 设计规范

### 1.1 通用约定

| 项目 | 规范 |
|------|------|
| 路径前缀 | `/api/v1/` |
| 内容类型 | `application/json` |
| 认证 | `X-API-Key` header（可选，由 `MPCHAT_API_KEY` 环境变量控制） |
| 超时 | LLM 相关端点 180s，其他端点 30s |
| 错误响应 | `{ "detail": "错误信息" }` 或 Pydantic 校验错误数组 |

### 1.2 LLM 端点通用请求字段

所有需要调用 LLM 的端点，请求体必须包含以下 4 个字段：

```python
provider: str = "openai"     # AI 服务商 ID（openai/anthropic/gemini 等）
model: str = "gpt-4o"        # 模型名称
api_key: str                 # 服务商 API Key（不可为空）
base_url: str = ""           # 自定义 Base URL（空则用服务商默认值）
```

### 1.3 错误处理约定

| HTTP 状态码 | 场景 | 响应体 |
|-------------|------|--------|
| 400 | 请求参数校验失败 | `{ "detail": [{ "loc": [...], "msg": "..." }] }` |
| 401 | API Key 无效 | `{ "detail": "API key required" }` |
| 422 | Pydantic 校验失败 | Pydantic 标准校验错误 |
| 500 | LLM 调用失败 / 内部错误 | `{ "detail": "具体错误描述" }` |
| 502 | 外部 API (Intercom/Medium/Paragraph) 调用失败 | `{ "detail": "External API error: ..." }` |

---

## 2. 新增 API 端点规格

### 2.1 翻译 API

#### `POST /api/v1/translate`

软文工作台翻译端点。

**请求体：**

```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "api_key": "sk-xxx",
  "base_url": "",
  "article": "# 标题\n\n正文内容...",
  "source_lang": "zh-CN",
  "target_lang": "en"
}
```

**响应体：**

```json
{
  "translated_article": "# Title\n\nBody content...",
  "source_lang": "zh-CN",
  "target_lang": "en"
}
```

**支持的语言代码：**

| 代码 | 语言 |
|------|------|
| `zh-CN` | 简体中文 |
| `zh-TW` | 繁体中文 |
| `en` | 英文 |

#### `POST /api/v1/external/translate`

外部文章翻译端点，请求/响应格式与 `/translate` 相同。

---

### 2.2 选题 API

#### `POST /api/v1/ideation/topics`

**请求体：**

```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "api_key": "sk-xxx",
  "base_url": "",
  "core_keyword": "crypto payment",
  "industry": "Web3",
  "count": 30
}
```

**响应体：**

```json
{
  "topics": [
    {
      "title": "10 Ways Crypto Payments Are Changing E-Commerce in 2026",
      "search_intent": "informational",
      "difficulty": "medium",
      "keywords": ["crypto payment", "e-commerce", "digital payment"]
    }
  ]
}
```

**字段说明：**

| 字段 | 类型 | 描述 |
|------|------|------|
| `title` | string | SEO 优化标题 |
| `search_intent` | enum | `informational` / `transactional` / `navigational` / `commercial` |
| `difficulty` | enum | `low` / `medium` / `high` |
| `keywords` | string[] | 相关长尾关键词（3-5 个） |

---

### 2.3 发布 API（扩展）

#### `POST /api/v1/publish/paragraph`

**请求体：** 复用 `PublishRequest`，额外使用 `api_key` 字段传递 Paragraph API Key。

**响应体：**

```json
{
  "ok": true,
  "url": "https://paragraph.xyz/@username/article-slug",
  "id": "article-id"
}
```

#### `POST /api/v1/publish/medium`（改造）

现有格式预览升级为 API 直发。

**请求体：** 复用 `PublishRequest`，使用 `token` 字段传递 Medium Integration Token。当 `token` 为空时降级为格式预览。

**响应体（直发成功）：**

```json
{
  "ok": true,
  "url": "https://medium.com/@username/article-slug-abc123",
  "id": "post-id"
}
```

**响应体（降级预览）：**

```json
{
  "ok": true,
  "preview": "---\ntitle: ...\n---\n\n文章内容..."
}
```

---

### 2.4 Intercom QA API

#### `POST /api/v1/intercom/generate-qa`

**请求体：**

```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "api_key": "sk-xxx",
  "base_url": "",
  "feature_description": "MPChat 支持多链加密支付...",
  "product_name": "MPChat",
  "tone": "professional",
  "count": 10
}
```

**响应体：**

```json
{
  "qa_pairs": [
    {
      "question": "What is MPChat?",
      "answer": "MPChat is a multi-chain crypto payment platform...",
      "category": "General"
    }
  ]
}
```

**tone 可选值：** `professional` / `friendly` / `technical` / `casual`

#### `POST /api/v1/intercom/upload`

**请求体：**

```json
{
  "intercom_token": "dG9rOm...",
  "collection_id": "123456",
  "title": "Getting Started with MPChat",
  "body": "<p>MPChat is...</p>"
}
```

**响应体：**

```json
{
  "ok": true,
  "id": "article-789",
  "url": "https://intercom.help/mpchat/en/articles/article-789"
}
```

---

## 3. 数据模型

### 3.1 新增 Pydantic 请求模型

```python
class TranslateRequest(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = Field(min_length=1)
    base_url: str = ""
    article: str = Field(min_length=1, max_length=100000)
    source_lang: str = Field(default="zh-CN")
    target_lang: str = Field(default="en")

class IdeationRequest(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = Field(min_length=1)
    base_url: str = ""
    core_keyword: str = Field(min_length=1)
    industry: str = ""
    count: int = Field(default=30, ge=5, le=50)

class IntercomQARequest(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = Field(min_length=1)
    base_url: str = ""
    feature_description: str = Field(min_length=1, max_length=50000)
    product_name: str = Field(default="MPChat")
    tone: Literal["professional", "friendly", "technical", "casual"] = "professional"
    count: int = Field(default=10, ge=3, le=30)

class IntercomUploadRequest(BaseModel):
    intercom_token: str = Field(min_length=1)
    collection_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
```

### 3.2 新增 Pydantic 响应模型

```python
class TranslateResponse(BaseModel):
    translated_article: str
    source_lang: str
    target_lang: str

class TopicSuggestion(BaseModel):
    title: str
    search_intent: str
    difficulty: str
    keywords: list[str]

class IdeationResponse(BaseModel):
    topics: list[TopicSuggestion]

class IntercomQAResponse(BaseModel):
    qa_pairs: list[dict]
```

### 3.3 新增 TypeScript 类型

```typescript
interface TranslateRequest {
  provider: string;
  model: string;
  api_key: string;
  base_url: string;
  article: string;
  source_lang: string;
  target_lang: string;
}

interface TranslateResponse {
  translated_article: string;
  source_lang: string;
  target_lang: string;
}

interface TopicSuggestion {
  title: string;
  search_intent: "informational" | "transactional" | "navigational" | "commercial";
  difficulty: "low" | "medium" | "high";
  keywords: string[];
}

interface IdeationRequest {
  provider: string;
  model: string;
  api_key: string;
  base_url: string;
  core_keyword: string;
  industry?: string;
  count?: number;
}

interface IdeationResponse {
  topics: TopicSuggestion[];
}

interface QAPair {
  question: string;
  answer: string;
  category: string;
}

interface IntercomQARequest {
  provider: string;
  model: string;
  api_key: string;
  base_url: string;
  feature_description: string;
  product_name?: string;
  tone?: "professional" | "friendly" | "technical" | "casual";
  count?: number;
}

interface IntercomQAResponse {
  qa_pairs: QAPair[];
}
```

---

## 4. Prompt 模板规范

### 4.1 翻译 Prompt

```
System: You are a professional translator specializing in tech/marketing content.

Rules:
1. Translate from {source_lang} to {target_lang}
2. Preserve ALL Markdown formatting: headings (H1-H6), lists, links, images, code blocks, bold/italic
3. Keep technical terms accurate (e.g., blockchain, DeFi, API)
4. Maintain the original tone and style
5. Do NOT add or remove content
6. Output ONLY the translated article, no explanations

User: {article}
```

### 4.2 选题 Prompt

```
System: You are an SEO content strategist. Generate {count} article title suggestions for the keyword "{core_keyword}".

Requirements:
1. Each title should target a specific long-tail keyword variation
2. Mix search intents: informational, transactional, navigational, commercial
3. Include difficulty estimation based on keyword competition
4. Titles should be compelling and click-worthy
5. Output as JSON array

{industry_context}

Output format:
[
  {{
    "title": "...",
    "search_intent": "informational|transactional|navigational|commercial",
    "difficulty": "low|medium|high",
    "keywords": ["keyword1", "keyword2", "keyword3"]
  }}
]
```

### 4.3 QA 生成 Prompt

```
System: You are a technical writer creating help center Q&A articles for {product_name}.

Tone: {tone}
Generate {count} Q&A pairs based on the following feature description.

Requirements:
1. Questions should be natural, as customers would ask them
2. Answers should be clear, concise, and actionable
3. Group by category (General, Setup, Troubleshooting, etc.)
4. Each answer should be 2-4 sentences
5. Output as JSON array

Feature Description: {feature_description}

Output format:
[
  {{
    "question": "...",
    "answer": "...",
    "category": "General|Setup|Usage|Troubleshooting|Billing|Security"
  }}
]
```

---

## 5. 环境变量新增

| 变量 | 功能 | 必需 | 默认值 |
|------|------|------|--------|
| `PARAGRAPH_API_KEY` | Paragraph 博客发布 | 否 | — |
| `MEDIUM_TOKEN` | Medium Integration Token | 否 | — |
| `INTERCOM_TOKEN` | Intercom Help Center API | 否 | — |

---

## 6. 前端 API 封装新增方法

```typescript
export const api = {
  // ... existing methods ...

  translate: (payload: TranslateRequest) =>
    request<TranslateResponse>("/api/v1/translate", {
      method: "POST",
      body: JSON.stringify(payload),
    }, 180000),

  translateExternal: (payload: TranslateRequest) =>
    request<TranslateResponse>("/api/v1/external/translate", {
      method: "POST",
      body: JSON.stringify(payload),
    }, 180000),

  generateTopics: (payload: IdeationRequest) =>
    request<IdeationResponse>("/api/v1/ideation/topics", {
      method: "POST",
      body: JSON.stringify(payload),
    }, 120000),

  generateIntercomQA: (payload: IntercomQARequest) =>
    request<IntercomQAResponse>("/api/v1/intercom/generate-qa", {
      method: "POST",
      body: JSON.stringify(payload),
    }, 120000),

  uploadToIntercom: (payload: {
    intercom_token: string;
    collection_id: string;
    title: string;
    body: string;
  }) =>
    request<{ ok: boolean; id: string; url: string }>("/api/v1/intercom/upload", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
```

---

## 6.1 前端翻译工具函数（`lib/translateUtils.ts`）

```typescript
// 自动检测源语言（供 ExternalClient 使用）
function detectSourceLang(
  text: string,
  stats: { cn: number; en: number }
): string
// 返回值之一：
//   "中文 (Chinese)" | "繁体中文 (Traditional Chinese)" | "英文 (English)"

// 根据源语言推导翻译目标按钮列表（供两个组件共享）
function getTranslateTargets(sourceLang: string): TranslateTarget[]
// TranslateTarget = { lang: string; labelKey: string }
//
// 映射规则：
//   中文           → [英文, 繁体中文]
//   英文           → [简体中文, 繁体中文]
//   繁体中文       → [简体中文, 英文]
//   其他           → [简体中文, 英文]
```

测试覆盖：`frontend/lib/__tests__/translateUtils.test.ts`，共 **21 个测试**全部通过。

---

## 7. 国际化 Key 新增清单

### 翻译功能 (Phase 1 + 增强)

| Key | 中文 | English |
|-----|------|---------|
| `btn.translateToZh` | 翻译为简体中文 | Translate to Simplified Chinese |
| `btn.translateToEn` | 翻译为英文 | Translate to English |
| `btn.translateToTw` | 翻译为繁体中文 | Translate to Traditional Chinese |
| `btn.translating` | 翻译中... | Translating... |
| `btn.copyTranslation` | 复制译文 | Copy Translation |
| `btn.downloadTranslation` | 下载译文 | Download Translation |
| `label.translate` | 一键翻译 | Quick Translate |
| `label.translateResult` | 翻译结果 | Translation |
| `msg.translateSuccess` | 翻译完成 | Translation complete |

### 发布渠道 (Phase 2)

| Key | 中文 | English |
|-----|------|---------|
| `publish.paragraph` | Paragraph | Paragraph |
| `publish.medium` | Medium | Medium |
| `publish.title` | 文章标题 | Article Title |
| `publish.enterToken` | 请输入 Token | Enter Token |

### 选题功能 (Phase 3)

| Key | 中文 | English |
|-----|------|---------|
| `nav.ideation` | 选题 | Ideation |
| `ideation.title` | SEO 选题助手 | SEO Topic Generator |
| `ideation.keyword` | 核心关键词 | Core Keyword |
| `ideation.industry` | 行业领域 | Industry |
| `ideation.count` | 生成数量 | Count |
| `ideation.generate` | 生成选题 | Generate Topics |
| `ideation.useTitle` | 使用此标题 | Use This Title |
| `ideation.intent` | 搜索意图 | Search Intent |
| `ideation.difficulty` | 难度 | Difficulty |
| `btn.aiIdeation` | AI 选题 | AI Ideation |

### QA 功能 (Phase 4)

| Key | 中文 | English |
|-----|------|---------|
| `nav.intercomQa` | QA 生成 | QA Generator |
| `qa.title` | 帮助中心 QA 生成 | Help Center QA Generator |
| `qa.featureDesc` | 功能描述 | Feature Description |
| `qa.productName` | 产品名称 | Product Name |
| `qa.tone` | 语气风格 | Tone |
| `qa.count` | 生成数量 | Count |
| `qa.generate` | 生成 QA | Generate QA |
| `qa.exportMd` | 导出 Markdown | Export Markdown |
| `qa.exportJson` | 导出 JSON | Export JSON |
| `qa.uploadIntercom` | 上传到 Intercom | Upload to Intercom |
| `qa.intercomToken` | Intercom Token | Intercom Token |
| `qa.collectionId` | Collection ID | Collection ID |
