# NipponClaw Design System

> 参考 EasyClaw 简洁风格，适配日本市场审美。深色优先，红色品牌，iOS 原生体验。

---

## 1. Visual Theme & Atmosphere

**风格定义：** 日式简约（和の簡潔）+ 现代科技感

- **深色优先**：主要界面使用深色模式，与 iOS 系统深色无缝融合
- **高对比度**：文字与背景对比清晰，符合无障碍标准（WCAG AA）
- **充足留白**：元素间保持足够呼吸空间，避免视觉拥挤
- **干净线条**：减少装饰性元素，功能即美学
- **品牌红点睛**：#E53935 仅用于关键交互点（CTA、logo、状态指示），不泛用

**设计参照：**
- EasyClaw 的内容密度与信息层级处理方式
- iOS Human Interface Guidelines（尤其是深色模式规范）
- 日本 UI 审美：无印良品、LINE 的简洁直白

---

## 2. Color Palette & Roles

### 品牌色

| Token | Hex | 用途 |
|-------|-----|------|
| `brand.primary` | `#E53935` | N Logo、主按钮、关键高亮 |
| `brand.primaryDark` | `#C62828` | 按压状态 |
| `brand.primaryLight` | `#EF5350` | 浅色模式辅助 |

### 背景层级

| Token | 深色模式 | 亮色模式 | iOS 语义 |
|-------|---------|---------|---------|
| `bg.primary` | `#000000` | `#FFFFFF` | `systemBackground` |
| `bg.grouped` | `#000000` | `#F2F2F7` | `systemGroupedBackground` |
| `surface` | `#1C1C1E` | `#FFFFFF` | `secondarySystemBackground` |
| `card` | `#2C2C2E` | `#FFFFFF` | `tertiarySystemBackground` |
| `elevated` | `#3A3A3C` | `#F2F2F7` | — |

### 文字色

| Token | 深色模式 | 亮色模式 | iOS 语义 |
|-------|---------|---------|---------|
| `text.primary` | `#FFFFFF` | `#000000` | `label` |
| `text.secondary` | `#8E8E93` | `#3C3C43` | `secondaryLabel` |
| `text.tertiary` | `#48484A` | `#C7C7CC` | `tertiaryLabel` |
| `text.placeholder` | `#636366` | `#C7C7CC` | `placeholderText` |
| `text.link` | `#E53935` | `#E53935` | — |

### 系统语义色

| Token | Hex | iOS 语义 |
|-------|-----|---------|
| `status.success` | `#34C759` | `systemGreen` |
| `status.error` | `#FF3B30` | `systemRed` |
| `status.warning` | `#FF9500` | `systemOrange` |
| `status.info` | `#007AFF` | `systemBlue` |

### 分隔与边框

| Token | 深色模式 | 亮色模式 |
|-------|---------|---------|
| `separator` | `#38383A` | `#C6C6C8` |
| `border` | `#3A3A3C` | `#D1D1D6` |

---

## 3. Typography Rules

### 字体

- **Primary:** SF Pro（系统默认，完整支持日文 CJK 字符）
- **Fallback:** Hiragino Sans（日文）→ Apple SD Gothic Neo（韩文）→ PingFang SC（中文）
- 禁止引入第三方字体，保持原生 iOS 文字渲染质量

### 字阶（iOS Dynamic Type）

| 角色 | SwiftUI Style | 参考尺寸 | 字重 | 用途 |
|------|--------------|---------|------|------|
| Large Title | `.largeTitle` | 34pt | Regular | 页面标题（如 Home） |
| Title | `.title` | 28pt | Bold | 区块标题 |
| Title 2 | `.title2` | 22pt | Regular | 次级标题 |
| Headline | `.headline` | 17pt | Semibold | 列表项标题、卡片头 |
| Body | `.body` | 17pt | Regular | 正文内容 |
| Callout | `.callout` | 16pt | Regular | 说明文字 |
| Subheadline | `.subheadline` | 15pt | Regular | 次级说明 |
| Footnote | `.footnote` | 13pt | Regular | 注释、时间戳 |
| Caption | `.caption` | 12pt | Regular | 标签、角标 |
| Caption 2 | `.caption2` | 11pt | Regular | 极小信息 |

### N Logo 字型

- 字符：`"N"`
- 字重：System Bold（`.fontWeight(.bold)`）
- 颜色：`Color.white`
- 背景：品牌红圆形（`#E53935`），无额外装饰

### 排版规则

- 行高：正文使用系统默认行高，不手动设置 line spacing
- 字间距：不调整（日文字符间距已由系统优化）
- 对齐：正文左对齐（LTR），避免两端对齐（日文断行问题）

---

## 4. Component Styling

### 主按钮（Primary Button）

```swift
// 参考实现
.background(Color(hex: "#E53935"))
.foregroundColor(.white)
.cornerRadius(8)
.frame(minHeight: 44)
.padding(.horizontal, 16)
```

| 属性 | 值 |
|------|---|
| 背景色 | 品牌红 `#E53935` |
| 文字色 | 白色 |
| 圆角 | 8pt |
| 最小高度 | 44pt |
| 字重 | Semibold |
| 按压状态 | `#C62828`，scale 0.97 |
| 禁用状态 | 透明度 0.4 |

### 次级按钮（Secondary Button）

| 属性 | 值 |
|------|---|
| 背景色 | `card`（深色：`#2C2C2E`） |
| 文字色 | 品牌红 |
| 圆角 | 8pt |
| 边框 | 无 |

### 卡片（Card）

| 属性 | 值 |
|------|---|
| 背景色 | `card` token |
| 圆角 | 12pt |
| 内边距 | 16pt |
| 间距 | 12pt |
| 阴影 | 无（通过背景色差异体现层级） |

### 输入框（Input Field）

| 属性 | 值 |
|------|---|
| 高度 | 44pt |
| 圆角 | 8pt |
| 背景 | `surface` |
| 边框 | `separator` 1pt |
| 内边距 | 水平 12pt |
| Focus 状态 | 品牌红边框 1.5pt |

### 导航栏（TabBar）

- iOS 标准 TabBar，3 个 Tab
- **Home**：主页/対話 — 消息气泡图标
- **Market**：市場 — 店铺图标
- **Settings**：設定 — 齿轮图标
- 选中色：品牌红 `#E53935`
- 未选中色：`text.secondary`

### Agent 头像（Agent Avatar）

| 尺寸 | 规格 |
|------|------|
| 大（详情页） | 60×60pt，圆形，品牌红背景，20pt "N" |
| 中（列表） | 40×40pt，圆形，品牌红背景，14pt "N" |
| 小（消息流） | 32×32pt，圆形，品牌红背景，12pt "N" |

### 状态指示点（Status Dot）

- 尺寸：8×8pt 实心圆
- 在线：`#34C759`
- 忙碌：`#FF9500`
- 离线：`#8E8E93`
- 错误：`#FF3B30`
- 位置：头像右下角

### Sheet / Modal

| 属性 | 值 |
|------|---|
| 遮罩 | 黑色 40% 透明度 |
| 内容背景 | `surface` |
| 圆角（顶部） | 16pt |
| 拖拽指示器 | `separator` 色，36×4pt，顶部 8pt |

---

## 5. Layout Principles

### 网格系统

- **基础单位：** 8pt 网格
- **水平边距：** 16pt（页面两侧）
- **Section 标题到内容：** 8pt
- **Section 间距：** 24pt
- **Card 间距：** 12pt
- **列表行高（最小）：** 44pt

### 间距速查

| 用途 | 值 |
|------|---|
| 紧凑（图标+文字）| 4pt |
| 标准（元素间）| 8pt |
| 宽松（组内）| 12pt |
| 区块内边距 | 16pt |
| Section 间距 | 24pt |
| 页面顶部留白 | 32pt |

### Safe Area

- 严格遵守 iOS Safe Area Insets
- 底部 Tab Bar 使用 `.ignoresSafeArea(.keyboard)` 处理键盘弹出
- 全屏内容（如聊天背景）使用 `.ignoresSafeArea(.all)`，但内容本身保留 safe area

### 聊天消息布局

- AI 消息：**全屏宽度**，无气泡，左对齐，水平边距 16pt
- 用户消息：右对齐气泡，最大宽度 80%，品牌红背景
- 参考：EasyClaw 的无气泡 AI 消息风格

---

## 6. Depth & Elevation

### 层级哲学

日式简约原则：**通过背景色差异和分隔线创造层级，而非阴影。**

| 层级 | 背景色（深色） | 用途 |
|------|-------------|------|
| Level 0 | `#000000` | 页面根背景 |
| Level 1 | `#1C1C1E` | 分组容器、Surface |
| Level 2 | `#2C2C2E` | 卡片、列表项 |
| Level 3 | `#3A3A3C` | 悬浮元素、Popover |

### 阴影使用

- **原则：最小化**
- 仅在绝对必要时（如浮动按钮、Toast）使用轻微阴影
- 阴影参数（如必须使用）：`color: black.opacity(0.3), radius: 8, x: 0, y: 4`

### Modal 遮罩

```swift
Color.black.opacity(0.4)
    .ignoresSafeArea()
```

---

## 7. Do's and Don'ts

### DO ✓

| 规则 | 原因 |
|------|------|
| 使用语义化颜色 token（`Color(.systemBackground)`） | 自动适配深色/亮色模式 |
| 支持 iOS Dynamic Type（系统字号缩放） | 无障碍访问，日本用户重视 |
| 所有触摸目标 ≥ 44×44pt | iOS HIG 标准，防止误触 |
| 所有文案使用 `lang.t()` 四语言包装 | 支持 EN/ZH/JA/KO |
| 测试深色和亮色两种模式 | 品牌一致性 |
| 为日文字符预留额外空间（+20% 宽度） | 日文 CJK 字符通常更宽 |
| 使用 `.accessibilityLabel()` 注释图标按钮 | VoiceOver 支持 |

### DON'T ✗

| 禁止 | 原因 |
|------|------|
| `Color.white` / `Color.black` 硬编码 | 不适配深色模式切换 |
| 超过 2 种字重组合（在同一组件内） | 视觉噪音，显得混乱 |
| 忽略 Safe Area（尤其底部） | 内容被 Home Indicator 遮挡 |
| 在非品牌场景滥用 `#E53935` | 稀释品牌识别度 |
| 使用半像素边框（0.5pt）| 日文字符相邻时渲染异常 |
| 自动播放动画（无用户触发） | 日本用户偏好安静界面 |
| 在消息流中使用全屏 AI 气泡 | 与品牌全宽无气泡风格冲突 |

---

## 8. Responsive Behavior

### iPhone 布局

**单列原则：** iPhone 所有页面默认单列布局

| 页面 | 布局方式 |
|------|---------|
| Home（Chat） | 全宽 ScrollView，消息垂直堆叠 |
| Market | **2列网格**（LazyVGrid，列间距 12pt） |
| Settings | 分组 List，iOS 标准样式 |
| Skills Panel | 底部 Sheet，可滑动网格 |

### 触摸目标

| 元素 | 最小尺寸 |
|------|---------|
| 按钮 | 44×44pt |
| 列表行 | 44pt 高 |
| 图标按钮 | 44×44pt（视觉可小，触摸区域补足） |
| Tab Bar 图标 | 系统默认（约 49pt 高） |

### 键盘处理

- 聊天输入框：键盘弹出时整体上移，保留输入框可见
- 使用 `.ignoresSafeArea(.keyboard)` 或 `KeyboardAwarePadding`
- 键盘收起动画：与系统键盘动画曲线同步

### 屏幕尺寸适配

| 设备 | 考虑点 |
|------|-------|
| iPhone SE（375pt）| Market 2列仍可用（每列约 170pt） |
| iPhone 15 Pro（393pt）| 标准设计基准 |
| iPhone 15 Pro Max（430pt）| 水平边距自适应扩展至 20pt |

---

## 9. Agent Prompt Guide

> 当向 AI（Claude 等）描述 NipponClaw 界面时，使用以下标准描述，确保输出一致。

### 品牌识别

```
Brand color: #E53935 (NipponClaw Red)
N Logo: Circle with brand red (#E53935) background, white bold "N" centered
App name: NipponClaw / 日本爪 (formal) / NC (abbreviated)
```

### 颜色描述

```
Dark mode background: #000000 (pure black, like iOS dark mode)
Surface: #1C1C1E (iOS secondarySystemBackground dark)
Card: #2C2C2E (iOS tertiarySystemBackground dark)
Primary text: #FFFFFF
Secondary text: #8E8E93 (iOS secondaryLabel)
Separator: #38383A
```

### 组件描述模板

```
// 主按钮
"brand red (#E53935) filled button, white semibold text, 8pt corners, 44pt height"

// 卡片
"dark card (#2C2C2E), 12pt rounded corners, 16pt padding, no shadow"

// Agent 头像
"40pt circle, brand red (#E53935) background, white bold N, status dot bottom-right"

// AI 消息
"full-width, no bubble, left-aligned text on transparent background, 16pt horizontal padding"

// 用户消息
"right-aligned bubble, brand red (#E53935) background, white text, 16pt corners, max 80% width"
```

### 多语言规范

```
所有 UI 文字必须通过 lang.t() 包装
支持语言：EN（英文）/ ZH（简中）/ JA（日文）/ KO（韩文）
优先级：用户系统语言 → JA（日本市场默认）

示例：
lang.t("home.title")          // "Home" / "主页" / "ホーム" / "홈"
lang.t("market.title")        // "Market" / "市场" / "マーケット" / "마켓"
lang.t("settings.title")      // "Settings" / "设置" / "設定" / "설정"
```

### 设计意图描述

```
Style: Japanese minimalism meets modern tech
Mood: Clean, calm, trustworthy, professional
Inspiration: EasyClaw's content-first approach + iOS native patterns
Key differentiator: Full-width AI messages (no bubble), brand red as accent only
```

---

*Last updated: 2026-04-07 — NipponClaw Design System v1.0*
