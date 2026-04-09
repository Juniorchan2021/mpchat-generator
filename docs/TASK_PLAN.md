# MPChat 软文机器人 — 功能扩展实施计划

> 最后更新：2026-03-18 | Phase 1 ✅ Phase 2 ✅ Phase 3 ✅（SEO 选题助手，28 个测试）

---

## 总览

本文档描述 4 个新功能的后端 + 前端详细实施步骤。每个 Phase 按依赖顺序排列，可独立交付。

| Phase | 功能 | 复杂度 | 新建文件 | 修改文件 | 状态 |
|-------|------|--------|---------|---------|------|
| 1 | 长文多语言翻译 | ★★☆ | 2 | 8 | ✅ 已完成 |
| 2 | 扩展发布渠道 (Paragraph + Medium) | ★★☆ | 0 | 6 | ✅ 已完成 |
| 3 | SEO 批量选题助手 | ★★★ | 4 | 6 | ✅ 已完成 |
| 4 | Intercom QA 生成 | ★★★ | 4 | 6 | ✅ 已完成 |

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
- [x] 工作台：翻译按钮根据 `form.language` 动态显示（中文→英文+繁中；英文→简中+繁中；其他→简中+英文）
- [x] 外部文章：自动识别源语言并动态显示翻译目标按钮，标题旁显示检测到的语言标签
- [x] 外部文章：`source_lang` 从硬编码"中文"改为自动检测值，繁体→简体翻译方向正确

---

## Phase 2：扩展长文发布渠道 ✅

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

- [x] Paragraph 发布成功并返回文章 URL（23 个单元测试覆盖）
- [x] Medium API 直发 draft 和 public 状态（Bearer Token 认证，两步流程）
- [x] Medium 无 token 时降级为格式预览
- [x] 外部文章页面新增发布面板（支持 Dev.to / Hashnode / Medium / Paragraph）
- [x] 发布失败时显示有意义的错误信息
- [x] 前端构建无错误，TypeScript 严格模式通过
- [x] i18n 中英双语同步（106 个 key）

---

## Phase 3：SEO 批量选题助手 ✅

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

- [x] 输入关键词后生成 5-50 个标题建议（滑块控制）
- [x] 每个标题显示搜索意图、难度、关键词（pill 展示）
- [x] 点击「使用此标题」通过 localStorage 跳转工作台并自动填入关键词
- [x] 工作台关键词旁「AI 选题」快捷链接，导航到 /ideation 页面
- [x] 导航栏新增「选题」入口
- [x] 后端 28 个测试全部通过（build_ideation_prompt / parse_topics / generate_topics）
- [x] 前端构建零错误，TypeScript 严格通过
- [x] i18n 126 keys 中英完全同步

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

- [x] 输入功能描述后生成 QA 列表
- [x] QA 列表可逐项编辑（问题/答案/分类均可修改）
- [x] 导出 Markdown 和 JSON 格式正确
- [x] Intercom 上传成功（需要有效 token）
- [x] 上传失败时显示有意义的错误信息
- [x] 前端构建零错误，TypeScript 严格模式通过
- [x] 后端 55 个测试全部通过
- [x] i18n 中英双语同步
- [x] 导航栏新增「QA 生成」入口

### Phase 4 问题修复记录

| 问题描述 | 原因 | 修复方案 | 状态 |
|---------|------|---------|------|
| 回答框直接显示 HTML 标签（`<p>`, `<strong>`, `<li>` 等），中文运营无法阅读 | 最初 Prompt 要求 LLM 直接输出 HTML 格式回答，运营人员在编辑区看到原始标签 | 将 Prompt 改为要求纯文本（no HTML tags）；上传 Intercom 前调用新增的 `plaintext_to_html()` 函数自动转换（段落→`<p>`，`- / *`→`<ul><li>`，`1.`→`<ol><li>`） | ✅ 已修复 |
| 只生成一个语言版本，三语言帮助中心需要分别手动触发三次，效率低 | 原始设计每次调用只生成单语言 QA 列表 | `build_qa_generation_prompt()` 新增 `languages` 参数，Prompt 改为要求 LLM 一次输出多语言嵌套 JSON `{"zh": [...], "zh-TW": [...], "en": [...]}`；新增 `parse_qa_result()` 解析多语言结构；`generate_qa_pairs()` 返回类型从 `list[dict]` 改为 `dict[str, list[dict]]` | ✅ 已修复 |
| 前端仅有单一 QA 列表，三语言混在一起无法区分 | 原始 UI 设计为单语言平铺展示 | 结果区改为三 Tab（简体中文/繁体中文/English），每个 Tab 独立编辑、导出；上传区为三语言分别配置 Collection ID + 独立「全部上传」按钮，并显示上传进度（已上传/总数） | ✅ 已修复 |
| Intercom 上传不支持语言标识，三语言内容上传后无法区分 locale | 原始 `upload_to_intercom()` 无 `locale` 参数，Intercom API payload 中缺少 `locale` 字段 | `upload_to_intercom()` 新增 `locale` 参数（默认 `"zh"`），上传时自动填入 Intercom API 的 `locale` 字段；`IntercomUploadRequest` 同步新增 `locale` 字段（默认 `"zh"`） | ✅ 已修复 |
| Collection 板块手动输入 ID，运营不知道自己账号下有哪些 Collection，容易填错 | 原设计使用静态文本输入框，Collection 来源不明、无法验证 | 新增 `fetch_intercom_collections()` 核心函数，调用 `GET /help_center/collections`；新增后端端点 `GET /api/v1/intercom/collections?token=xxx`；前端上传区新增「读取 Collections」按钮，成功后将文字输入框替换为下拉选单，每语言按对应 `translated_content[locale]` 显示名称 | ✅ 已修复 |

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

---

## Phase 3 问题修复记录

| 问题描述 | 原因 | 修复方案 | 状态 |
|---------|------|---------|------|
| 选题页：切换服务商后模型无法切换（仍为文本输入框） | `PROVIDER_DEFAULTS` 未包含 `models` 列表，模型字段为 `<input>` 而非 `<select>` | 在 `IdeationClient.tsx` 的 `PROVIDER_DEFAULTS` 中为每个服务商添加 `models[]`，当 models 非空时渲染 `<select>` 下拉 | ✅ 已修复 |
| 选题页/工作台/外部文章：API Key 输入框为 `type="password"`，无法查看输入是否正确 | 所有 API Key 字段均设置了 `type="password"` 且没有切换按钮 | 在 `IdeationClient.tsx`、`WorkspaceClient.tsx`、`ExternalClient.tsx` 的 API Key 字段旁添加 👁/🙈 切换按钮，控制 `type="text"/"password"` 切换 | ✅ 已修复 |
| 选题页：选择 Gemini 服务商时，"获取" Key 链接指向错误页面 | `IdeationClient.tsx` 中 Gemini 的 `get_key_url` 未配置，工作台读取的是 `config.json` 中的配置但 Ideation 是本地常量 | 在 `IdeationClient.tsx` 的 `PROVIDER_DEFAULTS` 中为 Gemini 设置正确的 `get_key_url: "https://aistudio.google.com/app/apikey"` | ✅ 已修复 |
| 输入中文关键词后生成的标题仍为英文 | `core/ideation.py` 的 prompt 硬编码要求"英文博客标题" | 在 `build_ideation_prompt()` 增加 `language` 参数（默认 `"auto"`），`auto` 模式自动检测关键词中文字符决定语言；同步更新 `IdeationRequest` 模型和前端 `IdeationClient.tsx` 添加语言选择器 | ✅ 已修复 |
| 点击"使用此标题"跳转工作台后，没有明确的"基于此标题生成文章"入口 | 工作台只接收了 `keywords` prefill，没有展示目标标题，也没有快捷生成按钮 | `WorkspaceClient.tsx` 读取 `mpchat-ideation-prefill` 时同时保存 `ideationTargetTitle`，并渲染一条紫色 banner 显示目标标题、内附"立即生成"按钮 | ✅ 已修复 |
| 离开选题页再返回后，之前生成的选题列表消失 | `IdeationClient.tsx` 的 `topics` 状态只存在于内存，路由跳转后组件销毁 | 新增 `mpchat-ideation-topics` localStorage key，每次 `topics` 更新时同步写入；组件挂载时恢复缓存，并显示"缓存自: xxx关键词"提示 | ✅ 已修复 |
| 外部文章页：AI 配置中模型字段为纯文本输入框，无法选择 gemini-2.5-pro 等其他模型 | `ExternalClient.tsx` 的 `PROVIDER_DEFAULTS` 类型定义缺少 `models[]` 字段，模型字段使用 `<input>` 渲染 | 为 `PROVIDER_DEFAULTS` 中每个服务商添加 `models[]` 列表，将模型字段改为条件渲染：有 models 时用 `<select>` 下拉，`custom` 保留 `<input>` | ✅ 已修复 |
| 选题页/外部文章页的 AI 服务商模型列表硬编码在前端，新版本模型（如 Gemini 3.x、Claude 5.x）发布后用户无法选择，且不同页面维护多份重复的 PROVIDER_DEFAULTS | 选题页和外部文章页在开发时各自独立维护了前端常量，与工作台的后端驱动模式不一致 | 删除两个页面的硬编码 `PROVIDER_DEFAULTS`，改为调用 `api.getConfig()` 读取与工作台同源的后端数据；`custom` 服务商（models 为空）自动降级为文本输入框，用户可输入任意模型名；`FALLBACK_CONFIG` 同步更新为离线兜底 | ✅ 已修复 |
| 各服务商在 `core/providers.py` 和 `fallbackConfig.ts` 中的模型列表已过时（如 Gemini 缺少 2.5-pro，OpenAI 缺少 gpt-4.1/o3，Claude 缺少最新命名） | 模型列表在 Phase 1 开发时手动填写，之后未跟进各厂商的模型迭代 | 更新 `core/providers.py` 和 `fallbackConfig.ts`，补全截至 2026-03 的各服务商主力最新模型（Gemini 2.5-pro/flash、GPT-4.1/o3/o4-mini、Claude opus-4-5/sonnet-4-5、Qwen3 等） | ✅ 已修复 |
| 从选题页点击「使用此标题」跳转工作台后，点击主配置区「生成文章」按钮生成的是按场景配置的文章，而非基于所选标题的文章；两个生成入口（主按钮 + banner 立即生成）功能不同但视觉上无区分，造成误触 | banner「立即生成」调用 `handleGenerate()` 前会 `setIdeationTargetTitle("")` 清空标题，导致 `target_title` 未传入 LLM；主配置区按钮也调用同一个无参数函数，二者无差异 | 1. `GenerateRequest` 新增 `target_title?: string` 字段；2. `build_user_prompt()` 注入"目标标题（必须严格以此标题为 H1）"指令；3. banner「立即生成」将 `ideationTargetTitle` 作为参数传入 `handleGenerate(title)`，生成完成后自动清空；4. 主配置区按钮在有选题 banner 时显示"按场景生成（忽略选题）"并降低透明度，明确区分两个入口 | ✅ 已修复 |

---

## 部署上线问题修复记录

| 问题描述 | 原因 | 修复方案 | 状态 |
|---------|------|---------|------|
| GitHub Actions 推送失败：`refusing to allow an OAuth App to create or update workflow` | GitHub OAuth Token 缺少 `workflow` scope，无法推送 `.github/workflows/` 文件 | 执行 `gh auth refresh -s workflow` 刷新 Token 权限 | ✅ 已修复 |
| Cloudflare Pages 部署失败：`Input required and not supplied: apiToken` | GitHub Secrets 中缺少 `CLOUDFLARE_API_TOKEN`、`CLOUDFLARE_ACCOUNT_ID`、`CF_PAGES_PROJECT_NAME` | 通过 `gh secret set` 添加三个 Cloudflare 相关 Secret | ✅ 已修复 |
| Cloudflare Pages 部署失败：`Resource not accessible by integration` | `GITHUB_TOKEN` 缺少 `deployments: write` 权限 | `deploy.yml` 的 `deploy-frontend` job 添加 `permissions: { contents: read, deployments: write }` | ✅ 已修复 |
| 前端显示「使用离线配置」+「Invalid API key」，所有后端接口返回 401 | Render 上设置了 `MPCHAT_API_KEY` 环境变量，但前端构建时 `NEXT_PUBLIC_API_KEY` 未配置，请求无 `X-API-Key` header | `api/deps.py` 将认证改为显式启用：仅当 `MPCHAT_AUTH_ENABLED=true` 且 `MPCHAT_API_KEY` 非空时才校验，默认关闭 | ✅ 已修复 |
| 前端连接 `localhost:8000`，无法访问线上后端 | GitHub Secret `NEXT_PUBLIC_API_URL` 被错误设置为 `http://localhost:8000` | 更正为 `https://mpchat-api.onrender.com`，并在 `.cursorrules` 中记录正确部署地址防止再犯 | ✅ 已修复 |
| 图片显示 alt 文字而非实际图片，Placewise CDN 返回 404 | 图片兜底源 `img.placewise.io` 已失效 | `image_client.py` 将 Placewise CDN 替换为 LoremFlickr，并为 `search_pixabay`/`search_pexels` 添加 `logging.warning` | ✅ 已修复 |
| 文章图片全部来自低质量兜底源，未使用 Pixabay/Pexels | Render 上未设置 `PIXABAY_API_KEY`/`PEXELS_API_KEY`，且 Dashboard 找不到 `mpchat-api` 服务无法手动添加 | `api/routers/generate.py` 为 `os.getenv()` 添加默认值，Render 自动重新部署后生效 | ✅ 已修复 |
