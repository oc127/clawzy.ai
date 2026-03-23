# Clawzy iOS App - Xcode 设置指南

## 前置要求

- macOS 13+ 的 Mac 电脑
- Xcode 15+（从 App Store 免费下载）
- Apple ID（免费即可，真机测试需要）

---

## 第一步：创建 Xcode 项目

1. 打开 Xcode
2. 点击 **Create New Project**
3. 选择 **iOS → App**，点 Next
4. 填写信息：
   - **Product Name**: `Clawzy`
   - **Team**: 选你的 Apple ID（如果没有就点 Add Account 登录）
   - **Organization Identifier**: `ai.clawzy`（这样 Bundle ID 就是 `ai.clawzy.Clawzy`）
   - **Interface**: 选 **SwiftUI**
   - **Language**: 选 **Swift**
   - 不勾选 Core Data 和 Tests（暂时不需要）
5. 点 Next，保存位置随意（比如桌面）

## 第二步：导入源代码

项目创建后，Xcode 会自动生成一些文件。你需要用我们的代码替换它们：

1. 在 Xcode 左侧的文件导航栏中，**删除**自动生成的 `ClawzyApp.swift` 和 `ContentView.swift`（右键 → Delete → Move to Trash）

2. 打开 Finder，找到 `clawzy.ai/ios/Clawzy/` 文件夹

3. 把里面的这些文件夹 **全部拖进** Xcode 左侧的项目导航栏中（拖到 Clawzy 文件夹下面）：
   - `App/`
   - `Models/`
   - `Services/`
   - `Views/`
   - `Utilities/`

4. 拖入时会弹出对话框，确保勾选：
   - ☑️ **Copy items if needed**
   - ☑️ **Create groups**
   - Target 选中 **Clawzy**
   - 点 Finish

## 第三步：配置后端地址

打开 `Utilities/Constants.swift`，修改 `baseURL` 和 `wsBaseURL`：

```swift
// 本地开发（Mac 和 iPhone 在同一 WiFi 下）
// 把 YOUR_MAC_IP 换成你 Mac 的局域网 IP（在系统偏好 → 网络中查看）
static let baseURL = "http://YOUR_MAC_IP:8000"
static let wsBaseURL = "ws://YOUR_MAC_IP:8000"

// 部署到服务器后改成
// static let baseURL = "https://clawzy.ai"
// static let wsBaseURL = "wss://clawzy.ai"
```

## 第四步：允许 HTTP 访问（开发阶段）

开发阶段如果后端没有 HTTPS，需要允许 HTTP：

1. 在 Xcode 左侧点击项目名（蓝色图标）
2. 选择 **Clawzy** target
3. 点 **Info** tab
4. 在 **Custom iOS Target Properties** 中右键 → Add Row
5. 添加 `App Transport Security Settings`（类型 Dictionary）
6. 展开它，添加子项 `Allow Arbitrary Loads` = `YES`

⚠️ **上线前记得删掉这个设置，改用 HTTPS**

## 第五步：运行项目

1. 顶部选择模拟器（推荐 iPhone 15 Pro）
2. 点击 ▶️ 运行按钮（或按 Cmd + R）
3. 等待编译完成，模拟器会自动启动并显示登录页面

### 如果用真机测试：

1. 用数据线连接 iPhone
2. 第一次需要在 iPhone 上：设置 → 通用 → VPN与设备管理 → 信任你的开发者证书
3. 顶部选择你的 iPhone，点运行

---

## 项目文件结构说明

```
Clawzy/
├── App/                    # 应用入口
│   ├── ClawzyApp.swift     # @main 入口，初始化全局状态
│   ├── ContentView.swift   # 根视图，判断登录/未登录
│   └── MainTabView.swift   # 底部 Tab 导航
│
├── Models/                 # 数据模型（和后端 API 对应）
│   ├── User.swift          # 用户、登录/注册请求
│   ├── Agent.swift         # Agent 实体
│   ├── Chat.swift          # 对话、消息、WebSocket 协议
│   └── Credits.swift       # 积分、交易、AI 模型
│
├── Services/               # 业务逻辑层
│   ├── APIClient.swift     # 通用 HTTP 请求客户端（自动带 JWT）
│   ├── AuthManager.swift   # 认证状态管理（登录/注册/登出）
│   ├── AgentService.swift  # Agent CRUD 操作
│   └── ChatService.swift   # WebSocket 聊天（核心！）
│
├── Views/                  # SwiftUI 界面
│   ├── Auth/
│   │   ├── LoginView.swift
│   │   └── RegisterView.swift
│   ├── Dashboard/
│   │   ├── DashboardView.swift
│   │   └── CreateAgentView.swift
│   ├── Chat/
│   │   └── ChatView.swift  # 聊天界面 + 消息气泡
│   └── Settings/
│       └── SettingsView.swift
│
└── Utilities/              # 工具类
    ├── Constants.swift     # API 地址和路径配置
    └── KeychainHelper.swift # 安全存储 JWT token
```

---

## 核心概念简要说明

### SwiftUI
苹果的声明式 UI 框架，用 Swift 代码描述界面，类似 React。`@State` 管理本地状态，`@Published` + `@ObservedObject` 管理共享状态。

### 数据流
```
用户操作 → View 调用 Service 方法 → Service 通过 APIClient 请求后端
                                  → 更新 @Published 属性
                                  → SwiftUI 自动刷新 UI
```

### WebSocket 聊天流程
```
ChatView 出现 → ChatService.connect(agentId)
             → 建立 WebSocket 连接
用户发消息   → ChatService.sendMessage(text)
             → 通过 WebSocket 发送 JSON
服务端回复   → 收到 stream 类型消息 → 逐字追加到气泡
             → 收到 done 类型消息 → 更新积分余额
```

---

## 常见问题

**Q: 编译报错怎么办？**
A: 先试 Product → Clean Build Folder (Cmd+Shift+K)，然后重新 Build

**Q: 模拟器上无法连接后端？**
A: 确保后端已启动，如果用 localhost 注意模拟器可以直接访问 localhost，但真机需要用 Mac 的局域网 IP

**Q: 怎么看网络请求的日志？**
A: Xcode 底部的 Console 区域会显示 print 输出的日志
