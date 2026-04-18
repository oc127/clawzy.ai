---
name: mcporter
description: Bridge REST APIs and CLI tools to MCP protocol for Claude integration
version: 1.0.0
tags: [mcp, mcporter, bridge, rest-api, integration]
category: mcp
platform: all
triggers: [mcporter, MCP bridge, REST to MCP, API bridge, ツール統合, tool integration, MCPポート]
---

## 使用場面
既存の REST API や CLI ツールを MCP サーバーとして Claude に公開する、サードパーティサービスをツールとして統合する。

## MCPorter の概念
```
既存 REST API / CLI
    ↓ wrap
MCPorter (MCP サーバー)
    ↓ expose
Claude (MCP クライアント)
```

## REST API を MCP に変換
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import Tool, TextContent
import httpx

app = Server("api-porter")

# 外部 API を MCP ツールとして公開
@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_products",
            description="商品データベースを検索",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "検索クエリ"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="create_order",
            description="新しい注文を作成",
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "quantity": {"type": "integer"}
                },
                "required": ["product_id", "quantity"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    async with httpx.AsyncClient(base_url="https://api.myservice.com") as client:
        if name == "search_products":
            resp = await client.get("/products/search", params=arguments)
            return [TextContent(type="text", text=resp.text)]
        elif name == "create_order":
            resp = await client.post("/orders", json=arguments)
            return [TextContent(type="text", text=resp.text)]
```

## CLI コマンドを MCP に変換
```python
import subprocess

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="run_pytest",
            description="pytest を実行してテスト結果を返す",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "default": "."},
                    "verbose": {"type": "boolean", "default": False}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "run_pytest":
        cmd = ["pytest", arguments.get("path", ".")]
        if arguments.get("verbose"):
            cmd.append("-v")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        return [TextContent(type="text", text=output[:3000])]
```

## MCPorter 設定のデプロイ
```json
{
  "mcpServers": {
    "my-api": {
      "command": "python",
      "args": ["/path/to/mcporter_server.py"],
      "env": {
        "API_KEY": "xxxx",
        "BASE_URL": "https://api.myservice.com"
      }
    }
  }
}
```

## 注意事項
- 認証情報は環境変数で渡す（コードに埋め込まない）
- タイムアウトを適切に設定する（subprocess は特に重要）
- エラーは TextContent として返し、例外を投げない
- 入力バリデーションを必ず実装する

## 検証
Claude がカスタム MCP ツールを呼び出して結果が返れば完了。
