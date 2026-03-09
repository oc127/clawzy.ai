# Clawzy iOS App

SwiftUI iOS client for the Clawzy.ai platform.

## Requirements

- Xcode 16+
- iOS 17+
- Swift 5.10+

## Setup

### Option 1: Swift Package (recommended for development)

```bash
cd ios/Clawzy
swift build
```

### Option 2: Xcode Project

1. Open Xcode → File → New → Project → iOS App
2. Set product name to "Clawzy", bundle ID to `ai.clawzy.app`
3. Remove the auto-generated files and drag in the contents of `ios/Clawzy/`
4. Add Swift Package dependency: `https://github.com/kishikawakatsumi/KeychainAccess.git` (4.2.2+)
5. Build & Run

## Configuration

- **Debug:** Connects to `http://localhost:8000/api/v1`
- **Release:** Connects to `https://clawzy.ai/api/v1`
- Override via env var `CLAWZY_API_URL`

## Architecture

```
Clawzy/
├── App/                  # App entry point, root navigation
├── Models/               # Codable data models
├── Services/
│   ├── APIClient.swift        # REST client with auto-refresh
│   ├── AuthService.swift      # JWT + Keychain management
│   └── WebSocketClient.swift  # Real-time chat with reconnect
├── Views/
│   ├── Auth/             # Login, Register
│   ├── Dashboard/        # Agent list, create agent
│   ├── Chat/             # Chat interface (core)
│   ├── Billing/          # Credits & plans
│   └── Settings/         # Profile, password, logout
└── Utils/                # Configuration
```

## Features

- JWT authentication with Keychain storage
- Auto token refresh on 401
- WebSocket chat with streaming responses
- Exponential backoff reconnection
- Agent CRUD (create, start, stop, delete)
- Credit balance tracking
- Subscription plan viewing
