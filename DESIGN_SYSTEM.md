# MPChat v5 设计系统 — Apple HIG 风格

> 本文档是 MPChat v5 前端的**唯一视觉真相来源（Single Source of Truth）**。
> 所有前端组件、页面布局、交互动效均须严格遵循本规范。

---

## 目录

1. [设计原则](#1-设计原则)
2. [色彩系统](#2-色彩系统)
3. [字体排版](#3-字体排版)
4. [材质与深度](#4-材质与深度)
5. [形状与间距](#5-形状与间距)
6. [组件规范](#6-组件规范)（含 Loading / Empty / Error / Modal / Tooltip / Progress）
7. [交互与动效](#7-交互与动效)
8. [CSS 变量清单](#8-css-变量清单)
9. [响应式断点](#9-响应式断点)
10. [无障碍与可访问性](#10-无障碍与可访问性)

---

## 1. 设计原则

遵循 Apple Human Interface Guidelines 的三大核心原则：

### Clarity（清晰）

- 文字清晰可读，每个元素都有明确用途
- 使用充足的对比度和留白，避免视觉噪音
- 图标和标签直观明了，无需学习成本

### Deference（顺从）

- UI 服务于内容，不喧宾夺主
- 减少不必要的装饰元素，让用户聚焦生成结果
- 流畅的动效引导注意力，而非分散注意力

### Depth（深度）

- 通过层级、半透明、阴影传达空间关系
- 毛玻璃材质暗示前后层级
- 微妙的阴影和边框区分可交互与静态元素

---

## 2. 色彩系统

采用深色模式（Dark Mode）为主色调，贴合 macOS Sonoma / iOS 17 暗色风格。

### 2.1 背景层级

| Token | 色值 | 用途 |
|-------|------|------|
| `--bg-base` | `#000000` | 页面最底层背景 |
| `--bg-elevated` | `#1C1C1E` | 卡片、面板背景 |
| `--bg-elevated-2` | `#2C2C2E` | 弹窗、浮层背景 |
| `--bg-hover` | `#3A3A3C` | 元素 hover 态背景 |
| `--bg-active` | `#48484A` | 元素按压态背景 |

### 2.2 主色与强调色

| Token | 色值 | 用途 |
|-------|------|------|
| `--primary` | `#0A84FF` | 主操作按钮、链接、选中态 |
| `--primary-hover` | `#409CFF` | 主色 hover 态 |
| `--primary-active` | `#0071E3` | 主色按压态 |
| `--accent-green` | `#30D158` | 成功状态、高分标识 |
| `--accent-orange` | `#FF9F0A` | 警告状态、中等分数 |
| `--accent-red` | `#FF453A` | 错误状态、低分标识 |
| `--accent-purple` | `#BF5AF2` | GEO 分析标识色 |
| `--accent-teal` | `#64D2FF` | 信息提示 |

### 2.3 文字层级

| Token | 色值 | 用途 |
|-------|------|------|
| `--text-primary` | `#F5F5F7` | 标题、正文主文字 |
| `--text-secondary` | `#A1A1A6` | 辅助说明、描述 |
| `--text-tertiary` | `#6E6E73` | 占位符、禁用态文字 |
| `--text-on-primary` | `#FFFFFF` | 主色按钮上的文字 |

### 2.4 边框与分割线

| Token | 色值 | 用途 |
|-------|------|------|
| `--border-default` | `rgba(255, 255, 255, 0.08)` | 卡片边框、分割线 |
| `--border-hover` | `rgba(255, 255, 255, 0.15)` | hover 态边框 |
| `--border-focus` | `rgba(10, 132, 255, 0.6)` | 聚焦态边框（主色透明） |

### 2.5 评分色阶

评分环和分数显示使用以下阈值映射：

| 分数范围 | 颜色 | Token |
|----------|------|-------|
| 90 - 100 | `#30D158`（绿色） | `--accent-green` |
| 70 - 89 | `#FF9F0A`（橙色） | `--accent-orange` |
| 0 - 69 | `#FF453A`（红色） | `--accent-red` |

---

## 3. 字体排版

### 3.1 字体栈

```css
--font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Display",
  "SF Pro Text", "Helvetica Neue", "PingFang SC", "Noto Sans SC",
  sans-serif;

--font-mono: "SF Mono", "Fira Code", "JetBrains Mono",
  "Menlo", "Consolas", monospace;
```

- 优先使用系统 SF Pro 字体（macOS/iOS 原生）
- 中文回退到 PingFang SC / Noto Sans SC
- 代码展示使用等宽字体栈

### 3.2 字号与字重

| 层级 | 字号 | 字重 | 行高 | 字间距 | 用途 |
|------|------|------|------|--------|------|
| Display | 34px | 700 (Bold) | 1.2 | -0.02em | 页面大标题 |
| H1 | 28px | 600 (Semibold) | 1.3 | -0.02em | 模块标题 |
| H2 | 22px | 600 (Semibold) | 1.35 | -0.01em | 卡片标题 |
| H3 | 17px | 600 (Semibold) | 1.4 | 0 | 小节标题 |
| Body | 15px | 400 (Regular) | 1.6 | 0 | 正文 |
| Body Small | 13px | 400 (Regular) | 1.5 | 0 | 辅助文字、Badge |
| Caption | 11px | 400 (Regular) | 1.4 | 0.02em | 标签、时间戳 |
| Code | 13px | 400 (Regular) | 1.6 | 0 | 代码块、API 示例 |

### 3.3 排版规则

- 标题使用负字间距（letter-spacing: -0.02em）以模仿 Apple 的紧凑感
- 正文行高 1.6 保证可读性
- 中文文本不启用负字间距
- 代码块使用 `--font-mono` 并添加轻微背景色区分

---

## 4. 材质与深度

### 4.1 毛玻璃（Frosted Glass / Vibrancy）

MPChat 的核心视觉特征。用于侧边栏、顶栏、浮层等需要层级区分的场景。

| 层级 | `backdrop-filter` | `background-color` | 用途 |
|------|-------------------|---------------------|------|
| Thin | `blur(12px) saturate(150%)` | `rgba(28, 28, 30, 0.6)` | 下拉菜单、Tooltip |
| Regular | `blur(24px) saturate(180%)` | `rgba(28, 28, 30, 0.72)` | 侧边栏、顶栏 |
| Thick | `blur(40px) saturate(200%)` | `rgba(28, 28, 30, 0.85)` | 模态弹窗 |

```css
.glass-regular {
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  background-color: rgba(28, 28, 30, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
```

### 4.2 阴影

| Token | 值 | 用途 |
|-------|-----|------|
| `--shadow-sm` | `0 1px 2px rgba(0, 0, 0, 0.3)` | 小元素（Badge、小按钮） |
| `--shadow-md` | `0 4px 12px rgba(0, 0, 0, 0.4)` | 卡片、面板 |
| `--shadow-lg` | `0 8px 32px rgba(0, 0, 0, 0.5)` | 弹窗、下拉菜单 |
| `--shadow-xl` | `0 16px 48px rgba(0, 0, 0, 0.6)` | 模态对话框 |
| `--shadow-focus` | `0 0 0 4px rgba(10, 132, 255, 0.3)` | 聚焦环（Focus Ring） |

### 4.3 层级（z-index）

| Token | 值 | 用途 |
|-------|-----|------|
| `--z-base` | `0` | 普通内容 |
| `--z-sticky` | `10` | 粘性顶栏 |
| `--z-sidebar` | `20` | 侧边栏 |
| `--z-dropdown` | `30` | 下拉菜单 |
| `--z-modal` | `40` | 模态弹窗 |
| `--z-toast` | `50` | Toast 通知 |

---

## 5. 形状与间距

### 5.1 圆角（Squircle 风格）

Apple 使用连续性曲线圆角（Squircle），CSS 中用 `border-radius` 近似：

| Token | 值 | 用途 |
|-------|-----|------|
| `--radius-xs` | `6px` | Badge、小标签 |
| `--radius-sm` | `8px` | 输入框、小按钮 |
| `--radius-md` | `12px` | 卡片、面板 |
| `--radius-lg` | `16px` | 模态、大卡片 |
| `--radius-xl` | `20px` | 侧边栏、主容器 |
| `--radius-pill` | `999px` | 药丸按钮、标签 |

### 5.2 间距系统

基于 4px 基础单元，所有间距为 4 的倍数：

| Token | 值 | 用途 |
|-------|-----|------|
| `--space-1` | `4px` | 紧凑间距（图标与文字） |
| `--space-2` | `8px` | 小间距（行内元素间） |
| `--space-3` | `12px` | 输入框内边距 |
| `--space-4` | `16px` | 组件内边距、列表项间距 |
| `--space-5` | `20px` | 卡片内边距 |
| `--space-6` | `24px` | 区块间距 |
| `--space-8` | `32px` | 大区块间距 |
| `--space-10` | `40px` | 页面级间距 |
| `--space-12` | `48px` | 模块间距 |
| `--space-16` | `64px` | 页面顶部/底部边距 |

### 5.3 内容宽度

| Token | 值 | 用途 |
|-------|-----|------|
| `--sidebar-width` | `280px` | 侧边栏宽度 |
| `--sidebar-collapsed` | `64px` | 侧边栏折叠宽度 |
| `--content-max-width` | `1200px` | 内容区最大宽度 |
| `--topbar-height` | `52px` | 顶栏高度 |

---

## 6. 组件规范

### 6.1 按钮（Button）

#### Primary Button

```css
.btn-primary {
  background-color: var(--primary);
  color: var(--text-on-primary);
  border: none;
  border-radius: var(--radius-pill);
  padding: 10px 20px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-primary:hover {
  background-color: var(--primary-hover);
}
.btn-primary:active {
  background-color: var(--primary-active);
  transform: scale(0.97);
}
.btn-primary:focus-visible {
  box-shadow: var(--shadow-focus);
  outline: none;
}
```

- 药丸形（pill）圆角
- 按压时缩小至 97%
- 聚焦时显示蓝色焦点环

#### Secondary Button

```css
.btn-secondary {
  background-color: transparent;
  color: var(--primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-pill);
  padding: 10px 20px;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.2s ease;
}
.btn-secondary:hover {
  background-color: var(--bg-hover);
  border-color: var(--border-hover);
}
.btn-secondary:active {
  transform: scale(0.97);
}
```

#### Ghost Button

```css
.btn-ghost {
  background-color: transparent;
  color: var(--text-secondary);
  border: none;
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  font-size: 13px;
  transition: all 0.2s ease;
}
.btn-ghost:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}
```

#### 按钮尺寸

| 尺寸 | padding | font-size | 用途 |
|------|---------|-----------|------|
| Small | `6px 12px` | `13px` | 内联操作（复制、展开） |
| Medium | `10px 20px` | `15px` | 标准操作（默认） |
| Large | `14px 28px` | `17px` | 主要 CTA（生成文章） |

### 6.2 输入框（Input / Textarea）

```css
.input {
  background-color: var(--bg-elevated);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  font-size: 15px;
  font-family: var(--font-sans);
  transition: all 0.2s ease;
  width: 100%;
}
.input::placeholder {
  color: var(--text-tertiary);
}
.input:hover {
  border-color: var(--border-hover);
}
.input:focus {
  border-color: var(--primary);
  box-shadow: var(--shadow-focus);
  outline: none;
}
.input--error {
  border-color: var(--accent-red);
  box-shadow: 0 0 0 4px rgba(255, 69, 58, 0.2);
}
```

- Textarea 默认高度 120px，可拉伸（`resize: vertical`）
- 聚焦态有蓝色焦点环
- 错误态有红色焦点环

### 6.3 分段控制器（Segmented Control / Tab）

模仿 iOS 分段控制器，用于顶层页面导航：

```css
.segmented-control {
  display: inline-flex;
  background-color: rgba(118, 118, 128, 0.12);
  border-radius: var(--radius-sm);
  padding: 2px;
  gap: 0;
}
.segmented-control__item {
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  border-radius: calc(var(--radius-sm) - 2px);
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
}
.segmented-control__item--active {
  background-color: var(--bg-elevated);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}
```

- 选中项有浮起效果（背景色 + 阴影）
- 切换时滑块平滑移动（JS 控制 `transform: translateX`）
- 用于三个主页面切换：创作工作台 / 外部文章优化 / 生成历史

### 6.4 卡片（Card）

```css
.card {
  background-color: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  transition: all 0.2s ease;
}
.card:hover {
  border-color: var(--border-hover);
  box-shadow: var(--shadow-md);
}
.card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}
.card__title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}
.card__subtitle {
  font-size: 13px;
  color: var(--text-secondary);
}
```

### 6.5 评分环（Score Ring）

SVG 实现的圆环进度指示器，核心视觉元素：

```css
.score-ring {
  width: 80px;
  height: 80px;
  position: relative;
}
.score-ring__circle {
  fill: none;
  stroke-width: 6;
  stroke-linecap: round;
  transform: rotate(-90deg);
  transform-origin: center;
  transition: stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1);
}
.score-ring__bg {
  stroke: var(--bg-hover);
}
.score-ring__text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 22px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
```

- 圆环半径 35px，描边宽度 6px
- 进度动画使用 `stroke-dashoffset` + CSS transition
- 数字使用 `tabular-nums` 防止宽度抖动
- 颜色根据分数自动映射（§2.5 评分色阶）
- 尺寸变体：Small（48px）用于内联展示，Large（120px）用于详情页

### 6.6 Badge / 标签

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: var(--radius-xs);
  line-height: 1.4;
}
.badge--success {
  background-color: rgba(48, 209, 88, 0.15);
  color: var(--accent-green);
}
.badge--warning {
  background-color: rgba(255, 159, 10, 0.15);
  color: var(--accent-orange);
}
.badge--error {
  background-color: rgba(255, 69, 58, 0.15);
  color: var(--accent-red);
}
.badge--info {
  background-color: rgba(10, 132, 255, 0.15);
  color: var(--primary);
}
```

### 6.7 展开面板（Expander / Disclosure）

```css
.expander {
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: all 0.2s ease;
}
.expander__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
  user-select: none;
}
.expander__header:hover {
  background-color: var(--bg-hover);
}
.expander__chevron {
  transition: transform 0.25s ease;
}
.expander__chevron--open {
  transform: rotate(90deg);
}
.expander__body {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
  padding: 0 var(--space-4);
}
.expander__body--open {
  max-height: 2000px;
  padding: var(--space-3) var(--space-4) var(--space-4);
}
```

### 6.8 Select / 下拉选择

```css
.select {
  appearance: none;
  background-color: var(--bg-elevated);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: 10px 36px 10px 14px;
  font-size: 15px;
  background-image: url("data:image/svg+xml,..."); /* chevron-down icon */
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.select:hover {
  border-color: var(--border-hover);
}
.select:focus {
  border-color: var(--primary);
  box-shadow: var(--shadow-focus);
  outline: none;
}
```

### 6.9 Toast / 通知

```css
.toast {
  position: fixed;
  top: var(--space-5);
  right: var(--space-5);
  z-index: var(--z-toast);
  min-width: 300px;
  max-width: 420px;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  backdrop-filter: blur(24px) saturate(180%);
  background-color: rgba(28, 28, 30, 0.85);
  border: 1px solid var(--border-default);
  box-shadow: var(--shadow-lg);
  animation: toast-in 0.3s ease forwards;
}
@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateY(-12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

- 自动消失：成功 3s，错误 5s
- 支持手动关闭
- 最多同时显示 3 条，垂直堆叠


### 6.10 Loading / 骨架屏（Skeleton）

#### 按钮加载态

```css
.btn-primary--loading {
  pointer-events: none;
  opacity: 0.7;
  position: relative;
}
.btn-primary--loading::after {
  content: "";
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: var(--text-on-primary);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-left: var(--space-2);
  display: inline-block;
  vertical-align: middle;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
```

#### 骨架占位

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-elevated) 25%,
    var(--bg-elevated-2) 50%,
    var(--bg-elevated) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease infinite;
  border-radius: var(--radius-sm);
}
.skeleton--text {
  height: 14px;
  width: 100%;
  margin-bottom: var(--space-2);
}
.skeleton--text:last-child {
  width: 60%;
}
.skeleton--circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
}
.skeleton--card {
  height: 200px;
  border-radius: var(--radius-md);
}
@keyframes skeleton-shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```

- 文章生成中：显示 3-4 行文字骨架 + 1 个圆形评分骨架
- 配图加载中：显示图片占位骨架（保持 4:3 宽高比）
- 评分计算中：评分环显示灰色底环 + 中心 spinner

### 6.11 Empty 状态（空状态）

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-8);
  text-align: center;
}
.empty-state__icon {
  width: 64px;
  height: 64px;
  color: var(--text-tertiary);
  margin-bottom: var(--space-4);
  opacity: 0.5;
}
.empty-state__title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}
.empty-state__description {
  font-size: 15px;
  color: var(--text-secondary);
  max-width: 360px;
  margin-bottom: var(--space-6);
}
```

使用场景：

| 页面 | 图标 | 标题 | 描述 | 操作按钮 |
|------|------|------|------|----------|
| 创作工作台（未生成） | 文档图标 | 开始创作第一篇文章 | 选择场景和配置，点击生成按钮 | 无 |
| 生成历史（空） | 时钟图标 | 暂无历史记录 | 生成的文章会自动保存在这里 | 去创作 |
| 外部文章（未粘贴） | 粘贴图标 | 粘贴文章开始分析 | 支持 Markdown 格式的任意来源文章 | 无 |

### 6.12 Error 状态（错误卡片）

```css
.error-card {
  background-color: rgba(255, 69, 58, 0.08);
  border: 1px solid rgba(255, 69, 58, 0.2);
  border-radius: var(--radius-md);
  padding: var(--space-4) var(--space-5);
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}
.error-card__icon {
  color: var(--accent-red);
  flex-shrink: 0;
  margin-top: 2px;
}
.error-card__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--accent-red);
  margin-bottom: var(--space-1);
}
.error-card__message {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}
.error-card__retry {
  margin-top: var(--space-3);
}
```

错误类型与展示：

| 类型 | 标题 | 说明 |
|------|------|------|
| LLM 调用失败 | AI 服务暂时不可用 | 请检查 API Key 或稍后重试 |
| 网络错误 | 网络连接失败 | 请检查网络设置后重试 |
| 超时 | 请求超时 | 生成时间过长，请重试或减少批量数量 |
| 图片搜索失败 | 配图获取失败 | 文章已生成，配图可稍后重试 |

### 6.13 Modal / 对话框

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fade-in 0.2s ease;
}
.modal {
  background-color: var(--bg-elevated-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  max-width: 480px;
  width: 90%;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: var(--shadow-xl);
  animation: modal-enter 0.3s var(--ease-spring);
}
.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}
.modal__title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}
.modal__close {
  color: var(--text-tertiary);
  cursor: pointer;
  padding: var(--space-1);
  border-radius: var(--radius-xs);
}
.modal__close:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}
.modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  margin-top: var(--space-6);
}
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes modal-enter {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(8px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
```

- 弹窗进入使用 spring 缓动（弹性感）
- 背景遮罩 50% 黑色
- Escape 键关闭，点击遮罩关闭
- 使用场景：清空历史确认、API Key 配置、批量场景选择

### 6.14 Tooltip / 提示

```css
.tooltip {
  position: absolute;
  z-index: var(--z-dropdown);
  padding: var(--space-2) var(--space-3);
  font-size: 12px;
  color: var(--text-primary);
  background-color: var(--bg-elevated-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xs);
  box-shadow: var(--shadow-md);
  white-space: nowrap;
  pointer-events: none;
  animation: tooltip-in 0.15s ease;
}
.tooltip::before {
  content: "";
  position: absolute;
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: var(--bg-elevated-2);
}
@keyframes tooltip-in {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
```

- 延迟 300ms 显示，移出即消失
- 用于配置项帮助说明（如"SEO+GEO 模式同时优化两项指标"）
- 最大宽度 280px，超出自动换行

### 6.15 Progress Bar / 进度条

```css
.progress-bar {
  width: 100%;
  height: 4px;
  background-color: var(--bg-hover);
  border-radius: 2px;
  overflow: hidden;
}
.progress-bar__fill {
  height: 100%;
  background-color: var(--primary);
  border-radius: 2px;
  transition: width 0.3s var(--ease-default);
}
.progress-bar--indeterminate .progress-bar__fill {
  width: 40%;
  animation: progress-slide 1.5s ease infinite;
}
@keyframes progress-slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}
```

- 确定进度：批量生成（如 3/10 篇已完成 → 30%）
- 不确定进度：单篇生成中（使用 indeterminate 动画）
- 颜色：默认蓝色（`--primary`），完成时切换为绿色（`--accent-green`）

批量生成进度组件：

```css
.batch-progress {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background-color: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}
.batch-progress__text {
  font-size: 13px;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
```

---

## 7. 交互与动效

### 7.1 过渡时长

| Token | 值 | 用途 |
|-------|-----|------|
| `--duration-fast` | `0.15s` | 即时反馈（hover 色变、小图标） |
| `--duration-normal` | `0.25s` | 标准交互（按钮、输入框） |
| `--duration-slow` | `0.4s` | 大面积变化（面板展开、页面切换） |
| `--duration-extra` | `0.6s` | 复杂动画（评分环填充、模态进入） |

### 7.2 缓动函数

| Token | 值 | 用途 |
|-------|-----|------|
| `--ease-default` | `cubic-bezier(0.4, 0, 0.2, 1)` | 通用缓动 |
| `--ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | 元素退出 |
| `--ease-out` | `cubic-bezier(0, 0, 0.2, 1)` | 元素进入 |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 弹性效果（按钮按压回弹） |

### 7.3 核心交互模式

#### 按压缩放（Press Scale）

所有可点击元素在 `:active` 态缩小，提供触觉反馈：

```css
.interactive:active {
  transform: scale(0.97);
}
```

- 按钮：`scale(0.97)`
- 卡片：`scale(0.99)`
- 图标按钮：`scale(0.92)`

#### Hover 色变

```css
.interactive:hover {
  background-color: var(--bg-hover);
}
```

#### 聚焦环（Focus Ring）

键盘导航时显示（`:focus-visible`），鼠标点击不显示：

```css
.interactive:focus-visible {
  box-shadow: 0 0 0 4px rgba(10, 132, 255, 0.3);
  outline: none;
}
```

#### 评分环动画

```css
@keyframes score-fill {
  from { stroke-dashoffset: var(--circumference); }
  to { stroke-dashoffset: var(--target-offset); }
}
```

- 页面加载后延迟 200ms 开始
- 持续 1s，使用 `ease-out` 缓动
- 同时数字从 0 计数到目标值（JS `countUp`）

#### 页面切换

分段控制器切换页面时：

```css
.page-enter {
  animation: fade-up 0.3s var(--ease-out) forwards;
}
@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### 7.4 减少动效模式

尊重用户系统偏好，减少晕动症触发：

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 8. CSS 变量清单

以下是前端 `globals.css` 中定义的完整变量列表，所有组件必须引用变量而非硬编码色值：

```css
:root {
  /* ── 色彩：背景 ── */
  --bg-base: #000000;
  --bg-elevated: #1C1C1E;
  --bg-elevated-2: #2C2C2E;
  --bg-hover: #3A3A3C;
  --bg-active: #48484A;

  /* ── 色彩：主色 ── */
  --primary: #0A84FF;
  --primary-hover: #409CFF;
  --primary-active: #0071E3;

  /* ── 色彩：强调色 ── */
  --accent-green: #30D158;
  --accent-orange: #FF9F0A;
  --accent-red: #FF453A;
  --accent-purple: #BF5AF2;
  --accent-teal: #64D2FF;

  /* ── 色彩：文字 ── */
  --text-primary: #F5F5F7;
  --text-secondary: #A1A1A6;
  --text-tertiary: #6E6E73;
  --text-on-primary: #FFFFFF;

  /* ── 色彩：边框 ── */
  --border-default: rgba(255, 255, 255, 0.08);
  --border-hover: rgba(255, 255, 255, 0.15);
  --border-focus: rgba(10, 132, 255, 0.6);

  /* ── 字体 ── */
  --font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Display",
    "SF Pro Text", "Helvetica Neue", "PingFang SC", "Noto Sans SC",
    sans-serif;
  --font-mono: "SF Mono", "Fira Code", "JetBrains Mono",
    "Menlo", "Consolas", monospace;

  /* ── 圆角 ── */
  --radius-xs: 6px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-pill: 999px;

  /* ── 间距 ── */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;

  /* ── 阴影 ── */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);
  --shadow-xl: 0 16px 48px rgba(0, 0, 0, 0.6);
  --shadow-focus: 0 0 0 4px rgba(10, 132, 255, 0.3);

  /* ── z-index ── */
  --z-base: 0;
  --z-sticky: 10;
  --z-sidebar: 20;
  --z-dropdown: 30;
  --z-modal: 40;
  --z-toast: 50;

  /* ── 动效 ── */
  --duration-fast: 0.15s;
  --duration-normal: 0.25s;
  --duration-slow: 0.4s;
  --duration-extra: 0.6s;
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* ── 布局 ── */
  --sidebar-width: 280px;
  --sidebar-collapsed: 64px;
  --content-max-width: 1200px;
  --topbar-height: 52px;
}
```

---

## 9. 响应式断点

| Token | 值 | 说明 |
|-------|-----|------|
| `--bp-mobile` | `640px` | 手机竖屏 |
| `--bp-tablet` | `768px` | 平板竖屏 |
| `--bp-laptop` | `1024px` | 小笔记本 |
| `--bp-desktop` | `1280px` | 桌面 |
| `--bp-wide` | `1536px` | 大屏 |

### 响应式策略

```css
/* Mobile: 侧边栏隐藏，全宽布局 */
@media (max-width: 767px) {
  .sidebar { display: none; }
  .main-content { padding: var(--space-4); }
}

/* Tablet: 侧边栏可折叠 */
@media (min-width: 768px) and (max-width: 1023px) {
  .sidebar { width: var(--sidebar-collapsed); }
}

/* Desktop: 完整布局 */
@media (min-width: 1024px) {
  .sidebar { width: var(--sidebar-width); }
  .main-content { max-width: var(--content-max-width); }
}
```

---

## 10. 无障碍与可访问性

### 10.1 对比度

所有文字/背景组合须满足 WCAG 2.1 AA 标准：

| 组合 | 对比度 | 要求 |
|------|--------|------|
| `--text-primary` on `--bg-base` | 17.5:1 | AA (4.5:1) |
| `--text-primary` on `--bg-elevated` | 12.8:1 | AA (4.5:1) |
| `--text-secondary` on `--bg-base` | 6.2:1 | AA (4.5:1) |
| `--text-tertiary` on `--bg-base` | 3.8:1 | Large text only (3:1) |
| `--primary` on `--bg-base` | 5.3:1 | AA (4.5:1) |

### 10.2 键盘导航

- 所有交互元素可通过 Tab 键到达
- 聚焦态使用 `:focus-visible` 显示焦点环
- 分段控制器支持方向键切换
- Escape 关闭模态/下拉
- Enter/Space 触发按钮

### 10.3 ARIA 标签

- 评分环：`role="progressbar"` + `aria-valuenow` + `aria-valuemin` + `aria-valuemax`
- 分段控制器：`role="tablist"` + `role="tab"` + `aria-selected`
- Toast：`role="alert"` + `aria-live="polite"`
- 展开面板：`aria-expanded` + `aria-controls`

### 10.4 动效偏好

遵循 `prefers-reduced-motion: reduce`，禁用所有非必要动画（见 §7.4）。


---

## 11. v5.1 品牌与 Logo 规范

### 11.1 Logo 规格

- **来源**：mp.net 官网（`https://mp.net/Logo.png`）
- **导航栏尺寸**：高度 32px，等比缩放
- **Favicon**：16x16 和 32x32，保存为 `frontend/app/favicon.ico`
- **文件位置**：`frontend/public/mpchat-logo.svg`（或 .png）

### 11.2 品牌文字

- 主标题：**MPChat**（加粗，`--text-primary`）
- 副标题：**Content OS**（常规字重，`--text-secondary`）
- 组合方式：Logo + 主标题 + 副标题 水平排列，`gap: 12px`

### 11.3 导航栏最终布局

```
[Logo 32px] MPChat Content OS          工作台  外部文章  历史    中/EN
            ^^^^^^^^^^^^^^^^            ^^^ 当前页高亮 ^^^      ^^^ 语言切换
            品牌区域 (flex)              导航链接 (flex)          功能区 (flex)
```

- 品牌区域使用 `display: flex; align-items: center; gap: 12px`
- 导航链接：选中态使用 `--primary` 下划线或背景色
- 功能区包含语言切换按钮

---

## 12. 国际化 (i18n) UI 设计

### 12.1 语言切换按钮

- **位置**：导航栏最右侧，导航链接之后
- **样式**：Pill 形状，`border-radius: 20px`，`padding: 4px 12px`
- **两态**："中" / "EN"
- **背景**：`rgba(255,255,255,0.08)`，hover 时 `rgba(255,255,255,0.12)`
- **切换行为**：无页面刷新，React Context 实时更新所有文案
- **持久化**：`localStorage.setItem("mpchat-locale", locale)`

### 12.2 布局弹性适应

- 英文文案通常比中文长 30-50%
- 所有文案容器使用弹性布局（flexbox / grid），避免固定宽度
- 按钮使用 `min-width` 而非 `width`
- Tab 文字允许 `white-space: nowrap`

### 12.3 翻译覆盖范围

| 区域 | 中文示例 | 英文示例 |
|------|----------|----------|
| 导航 | 工作台 / 外部文章 / 历史 | Workspace / External Article / History |
| 表单标签 | AI 服务商 / 模型 / 关键词 | Provider / Model / Keywords |
| 按钮 | 生成文章 / 开始分析 / 复制 | Generate / Analyze / Copy |
| Tab | 文章内容 / SEO·GEO 分析 / 导出与复制 | Article / SEO·GEO / Export |
| 提示 | 服务器唤醒中... / 请输入关键词 | Server warming up... / Enter keywords |
| 空状态 | 还没有生成记录 | No history yet |
| 错误 | 请求失败：{detail} | Request failed: {detail} |

---

## 13. 外部文章配置条设计

### 13.1 设计目标

外部文章页面不再有独立的 API Key / Model / Base URL 输入框，改为使用共享配置条，继承工作台设置。

### 13.2 默认态（折叠）

```
┌──────────────────────────────────────────────────────────┐
│  🔧 AI 配置：Google Gemini / gemini-2.5-flash  ✓  [修改]│
└──────────────────────────────────────────────────────────┘
```

- **样式**：`rgba(25,25,30,0.6)` + `backdrop-filter: blur(12px)`
- **圆角**：`12px`
- **高度**：`48px`（单行紧凑）
- **绿色勾号**：`--accent-green` 表示已配置可用
- **"修改" 链接**：`--primary` 颜色，`cursor: pointer`

### 13.3 展开态

点击 "修改" 后，配置条高度动画展开（`max-height` transition），显示完整配置面板：

- Provider 下拉框（自动填充 Base URL）
- Model 下拉框
- API Key 输入框（`type="password"`）
- Base URL 输入框

展开/收起动画：`max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1)`

### 13.4 数据来源优先级

1. `localStorage["mpchat-ai-config"]`（工作台保存的配置）
2. 环境变量 `NEXT_PUBLIC_DEFAULT_GEMINI_KEY`（默认 Gemini Key）
3. 空值（用户需手动输入）

---

## 14. 冷启动提示设计

### 14.1 触发条件

- 用户点击任何需要后端响应的按钮（生成、优化、AI 检测等）
- 请求发出后超过 **5 秒** 未收到响应

### 14.2 视觉设计

```
┌──────────────────────────────────────────────────────────┐
│  ⏳ 服务器正在唤醒中，首次请求可能需要 30-60 秒...        │
└──────────────────────────────────────────────────────────┘
```

- **背景**：`rgba(99,91,255,0.15)`
- **圆角**：`12px`
- **动画**：脉冲呼吸效果 `@keyframes pulse { 0%,100% { opacity:0.7 } 50% { opacity:1 } }` 周期 2s
- **位置**：触发按钮下方，不遮挡内容
- **消失**：收到后端响应后 `opacity 0.3s` 淡出

### 14.3 页面预热机制

`layout.tsx` 挂载时静默调用 `GET /api/v1/health`，提前唤醒后端：

```typescript
useEffect(() => {
  fetch(`${API_URL}/api/v1/health`).catch(() => {});
}, []);
```

---

## 15. 默认 Key 状态指示

### 15.1 已配置默认 Key

- API Key 输入框 placeholder：`"已配置默认 Key（可覆盖）"`
- 输入框左侧小圆点：`--accent-green`
- 用户清空输入框后恢复默认值

### 15.2 无默认 Key（非 Gemini Provider）

- API Key 输入框 placeholder：`"请输入 API Key"`
- 输入框边框：`--accent-orange` 高亮提示
- 生成按钮 tooltip：`"请先配置 API Key"`
