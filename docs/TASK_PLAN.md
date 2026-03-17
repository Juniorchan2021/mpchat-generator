# MPChat 软文机器人 — 功能扩展实施计划

> 最后更新：2026-03-18 | Phase 1 已完成（commit: fd4f537）

---

## 总览

本文档描述 4 个新功能的后端 + 前端详细实施步骤。每个 Phase 按依赖顺序排列，可独立交付。

| Phase | 功能 | 复杂度 | 新建文件 | 修改文件 | 状态 |
|-------|------|--------|---------|---------|------|
| 1 | 长文多语言翻译 | ★★☆ | 2 | 8 | ✅ 已完成 |
| 2 | 扩展发布渠道 (Paragraph + Medium) | ★★☆ | 0 | 6 | ⬜ 待执行 |
| 3 | SEO 批量选题助手 | ★★★ | 4 | 6 | ⬜ 待执行 |
| 4 | Intercom QA 生成 | ★★★ | 4 | 6 | ⬜ 待执行 |

---

## Phase 1：长文多语言一键翻译 ✅

### 1.1 后端

#### Step 1 — 新建 `core/translate.py`

- 实现 `build_translate_prompt(article, source_lang, target_lang)` 函数
- Prompt 要求：保持 Markdown 格式不变，术语翻译准确，不丢失标题层级
- 复用 `core/generation.py` 中的 `call_llm()` 执行翻译

#### Step 2 — 新增请求/响应模型

- `api/models/requests.py`：新增 `TranslateRequest(BaseModel)`
  - 字段：`provider`, `model`, `api_key`, `base_url`, `article`, `source_lang`, `target_lang`
- `api/models/responses.py`：新增 `TranslateResponse(BaseModel)`
  - 字段：`translated_article`, `source_lang`, `target_lang`

#### Step 3 — 新建路由

- 新建 `api/routers/translate.py`
  - `POST /api/v1/translate` — 软文工作台翻译端点
- 修改 `api/routers/external.py`
  - 新增 `POST /api/v1/external/translate` — 外部文章翻译端点
- 修改 `api/main.py`：注册 `translate.router`

### 1.2 前端

#### Step 4 — 类型 & API 封装

- `frontend/lib/types.ts`：新增 `TranslateRequest`, `TranslateResponse` 类型
- `frontend/lib/api.ts`：新增 `translate()` 和 `translateExternal()` 方法

#### Step 5 — 工作台集成

- `frontend/components/WorkspaceClient.tsx`：
  - 在文章预览区域下方增加「翻译为英文」「翻译为繁体中文」按钮
  - 新增 `translatedArticle` 状态和 `handleTranslate()` 函数
  - 翻译结果以折叠面板展示

#### Step 6 — 外部文章集成

- `frontend/components/ExternalClient.tsx`：
  - 在优化后文章下方增加翻译按钮和结果展示

#### Step 7 — 国际化文案

- `frontend/lib/i18n/zh.json` + `en.json`：新增翻译相关 key

### 1.3 验证清单

- [x] 翻译中文文章为英文，Markdown 格式完整保留
- [x] 翻译中文文章为繁体中文，术语正确
- [x] 外部文章优化后可直接翻译
- [x] 错误处理：API Key 无效、空文章等边界情况（47 个测试全部通过）

---

## Phase 2：扩展长文发布渠道

### 2.1 后端

#### Step 1 — Paragraph 发布函数

- `publishers.py`：新增 `publish_to_paragraph(api_key, title, body_markdown, tags, canonical_url)`
- 调用 Paragraph API（REST），返回文章 URL

#### Step 2 — Medium 真实发布

- `publishers.py`：新增 `publish_to_medium(token, title, body_markdown, tags, canonical_url, publish_status)`
- 调用 Medium API `/v1/users/{userId}/posts`，支持 draft/public 状态
- 保留现有格式化预览作为降级方案

#### Step 3 — 路由 & 模型更新

- `api/routers/publish.py`：
  - 新增 `POST /api/v1/publish/paragraph` 端点
  - 修改 `POST /api/v1/publish/medium` 为真实发布（保留预览降级）
- `api/models/requests.py`：`PublishRequest` 增加 `medium_token` 字段

#### Step 4 — 环境变量

- `.env.example`：新增 `PARAGRAPH_API_KEY`, `MEDIUM_TOKEN`

### 2.2 前端

#### Step 5 — 工作台发布面板扩展

- `frontend/components/WorkspaceClient.tsx`：
  - `PLATFORMS` 数组增加 `{ id: "paragraph", label: "Paragraph", needsKey: true }`
  - Medium 条目改为 `needsKey: true`

#### Step 6 — 外部文章发布面板（新增）

- `frontend/components/ExternalClient.tsx`：
  - 新增发布面板区域，复用 WorkspaceClient 的发布逻辑
  - 增加标题输入框
  - 支持 Medium、Paragraph、Dev.to、Hashnode 发布

#### Step 7 — 国际化文案

- `frontend/lib/i18n/zh.json` + `en.json`：新增发布相关 key

### 2.3 验证清单

- [ ] Paragraph 发布成功并返回文章 URL
- [ ] Medium API 直发 draft 和 public 状态
- [ ] Medium 无 token 时降级为格式预览
- [ ] 外部文章页面可正常发布到所有平台
- [ ] 发布失败时显示有意义的错误信息

---

## Phase 3：SEO 批量选题助手

### 3.1 后端

#### Step 1 — 新建 `core/ideation.py`

- 实现 `build_ideation_prompt(core_keyword, industry, count)` 函数
- Prompt 输出 JSON 数组，每项含 `title`, `search_intent`, `difficulty`, `keywords`
- 复用 `call_llm()` + `robust_parse()`

#### Step 2 — 新增模型

- `api/models/requests.py`：新增 `IdeationRequest`
  - 字段：`provider`, `model`, `api_key`, `base_url`, `core_keyword`, `industry`(可选), `count`(默认 30)
- `api/models/responses.py`：新增 `IdeationResponse`
  - 字段：`topics: list[TopicSuggestion]`

#### Step 3 — 新建路由

- 新建 `api/routers/ideation.py`
  - `POST /api/v1/ideation/topics` 端点
- 修改 `api/main.py`：注册 `ideation.router`

### 3.2 前端

#### Step 4 — 类型 & API 封装

- `frontend/lib/types.ts`：新增 `TopicSuggestion`, `IdeationRequest`, `IdeationResponse`
- `frontend/lib/api.ts`：新增 `generateTopics()` 方法

#### Step 5 — 独立页面

- 新建 `frontend/app/ideation/page.tsx`：选题助手页面入口
- 新建 `frontend/components/IdeationClient.tsx`：选题助手主组件
  - 输入：核心关键词、行业（可选）、生成数量滑块
  - 输出：标题列表，每行可点击「使用此标题」跳转工作台
  - UI 风格：沿用 glass-card 设计体系

#### Step 6 — 工作台快捷入口

- `frontend/components/WorkspaceClient.tsx`：
  - 关键词输入框旁增加「AI 选题」按钮
  - 弹出迷你选题面板，选中标题后自动填入关键词和场景

#### Step 7 — 导航 & 国际化

- `frontend/components/HeaderClient.tsx`：导航增加「选题」入口
- `frontend/lib/i18n/zh.json` + `en.json`：新增选题相关 key

### 3.3 验证清单

- [ ] 输入关键词后生成 20-50 个标题建议
- [ ] 每个标题显示搜索意图、难度、关键词
- [ ] 点击「使用此标题」能正确跳转到工作台并自动填入
- [ ] 工作台迷你选题面板正常弹出和关闭
- [ ] 导航栏新入口样式一致

---

## Phase 4：Intercom QA 帮助中心生成

### 4.1 后端

#### Step 1 — 新建 `core/intercom_qa.py`

- 实现 `build_qa_generation_prompt(feature_description, product_name, tone, count)` 函数
- Prompt 输出 JSON 数组，每项含 `question`, `answer`, `category`
- 实现 `upload_to_intercom(token, collection_id, title, body)` — 调用 Intercom Help Center API

#### Step 2 — 新增模型

- `api/models/requests.py`：
  - `IntercomQARequest`：`provider`, `model`, `api_key`, `base_url`, `feature_description`, `product_name`, `tone`, `count`
  - `IntercomUploadRequest`：`intercom_token`, `collection_id`, `title`, `body`
- `api/models/responses.py`：新增 `IntercomQAResponse`
  - `qa_pairs: list[dict]`

#### Step 3 — 新建路由

- 新建 `api/routers/intercom_qa.py`
  - `POST /api/v1/intercom/generate-qa` — 生成 QA
  - `POST /api/v1/intercom/upload` — 上传到 Intercom
- 修改 `api/main.py`：注册 `intercom_qa.router`

#### Step 4 — 环境变量

- `.env.example`：新增 `INTERCOM_TOKEN`

### 4.2 前端

#### Step 5 — 类型 & API 封装

- `frontend/lib/types.ts`：新增 `QAPair`, `IntercomQARequest`, `IntercomQAResponse`
- `frontend/lib/api.ts`：新增 `generateIntercomQA()`, `uploadToIntercom()` 方法

#### Step 6 — 独立页面

- 新建 `frontend/app/intercom-qa/page.tsx`：页面入口
- 新建 `frontend/components/IntercomQAClient.tsx`：主组件
  - 输入：产品功能描述（多行文本）、产品名、语气风格、生成数量
  - 输出：QA 列表卡片，每项可编辑
  - 操作：导出 Markdown / JSON、一键上传 Intercom
  - UI 风格：沿用 glass-card 设计体系

#### Step 7 — 导航 & 国际化

- `frontend/components/HeaderClient.tsx`：导航增加「QA 生成」入口
- `frontend/lib/i18n/zh.json` + `en.json`：新增 QA 相关 key

### 4.3 验证清单

- [ ] 输入功能描述后生成 QA 列表
- [ ] QA 列表可逐项编辑
- [ ] 导出 Markdown 和 JSON 格式正确
- [ ] Intercom 上传成功（需要有效 token）
- [ ] 上传失败时显示有意义的错误信息

---

## 文件变更总汇

### 新建文件（10 个）

| 文件 | Phase | 用途 |
|------|-------|------|
| `core/translate.py` | 1 | 翻译 Prompt 构建 |
| `api/routers/translate.py` | 1 | 翻译 API 端点 |
| `core/ideation.py` | 3 | 选题 Prompt 构建 |
| `api/routers/ideation.py` | 3 | 选题 API 端点 |
| `frontend/app/ideation/page.tsx` | 3 | 选题页面入口 |
| `frontend/components/IdeationClient.tsx` | 3 | 选题主组件 |
| `core/intercom_qa.py` | 4 | QA Prompt + Intercom 上传 |
| `api/routers/intercom_qa.py` | 4 | QA API 端点 |
| `frontend/app/intercom-qa/page.tsx` | 4 | QA 页面入口 |
| `frontend/components/IntercomQAClient.tsx` | 4 | QA 主组件 |

### 修改文件（13 个）

| 文件 | Phase | 变更内容 |
|------|-------|---------|
| `api/main.py` | 1,3,4 | 注册 3 个新路由 |
| `api/models/requests.py` | 1,2,3,4 | 新增 4 个请求模型 |
| `api/models/responses.py` | 1,3,4 | 新增 3 个响应模型 |
| `api/routers/external.py` | 1 | 新增翻译端点 |
| `api/routers/publish.py` | 2 | 新增 Paragraph、改造 Medium |
| `publishers.py` | 2 | 新增 Paragraph + Medium 函数 |
| `.env.example` | 2,4 | 新增环境变量 |
| `frontend/lib/types.ts` | 1,3,4 | 新增 8+ 个类型 |
| `frontend/lib/api.ts` | 1,3,4 | 新增 5 个 API 方法 |
| `frontend/components/WorkspaceClient.tsx` | 1,2,3 | 翻译按钮 + 选题入口 + Paragraph |
| `frontend/components/ExternalClient.tsx` | 1,2 | 翻译按钮 + 发布面板 |
| `frontend/components/HeaderClient.tsx` | 3,4 | 导航增加 2 个入口 |
| `frontend/lib/i18n/zh.json` + `en.json` | 1,2,3,4 | 所有新增文案 |
