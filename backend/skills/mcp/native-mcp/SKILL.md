---
name: native-mcp
description: Use Model Context Protocol (MCP) tools for filesystem, web, and service access
version: 1.0.0
tags: [mcp, model-context-protocol, tools, server, filesystem]
category: mcp
platform: all
triggers: [MCP, Model Context Protocol, MCPツール, MCP server, mcp tool, tool calling, ツール呼び出し]
---

## 使用場面
ファイルシステムへのアクセス、外部サービスの呼び出し、ブラウザ操作、データベースアクセス。

## MCP の仕組み
```
Claude ←→ MCP Client ←→ MCP Server ←→ 外部リソース
                                        (ファイル, Web, DB)
```

## 主要な公式 MCP サーバー

### Filesystem MCP
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"]
    }
  }
}
```

利用可能なツール:
- `read_file` — ファイル読み取り
- `write_file` — ファイル書き込み
- `list_directory` — ディレクトリ一覧
- `search_files` — ファイル検索
- `create_directory` — ディレクトリ作成

### GitHub MCP
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxxx"}
    }
  }
}
```

### Brave Search MCP
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {"BRAVE_API_KEY": "BSAxxx"}
    }
  }
}
```

## カスタム MCP サーバーの作成（Python）
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import Tool

app = Server("my-skill-server")

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_weather",
            description="指定された都市の天気を取得",
            inputSchema={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_weather":
        city = arguments["city"]
        # 実際の天気 API を呼び出す
        return f"{city}の天気: 晴れ、気温 22℃"

if __name__ == "__main__":
    import asyncio
    asyncio.run(stdio_server(app))
```

## 設定ファイルの場所
```
# Claude Desktop
~/Library/Application Support/Claude/claude_desktop_config.json

# Claude Code
~/.claude/claude.json  # または .claude/settings.json (プロジェクト)
```

## 注意事項
- MCP サーバーはローカルプロセスとして動作（セキュア）
- `npx -y` で自動インストール・実行
- 許可するパスは最小限に設定する（Filesystem MCP）

## 検証
Claude に「利用可能なツールは何ですか？」と聞いてMCPツールが列挙されれば完了。
