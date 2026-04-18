---
name: linear
description: Create and manage Linear issues, projects, and sprints via Linear API
version: 1.0.0
tags: [linear, project-management, issue, sprint, task-tracking]
category: productivity
platform: all
triggers: [linear, Linear issue, リニア, プロジェクト管理, issue tracker, sprint, cycle, バックログ]
---

## 使用場面
Linear のイシュー作成・更新、スプリント管理、バックログ整理、チームの進捗追跡。

## Linear API 設定
```python
import httpx

LINEAR_API_KEY = "lin_api_xxxxxxxxxxxx"
HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json"
}
LINEAR_URL = "https://api.linear.app/graphql"

def linear_query(query: str, variables: dict = None):
    resp = httpx.post(LINEAR_URL, headers=HEADERS, json={
        "query": query,
        "variables": variables or {}
    })
    return resp.json()
```

## イシューの作成
```python
CREATE_ISSUE = """
mutation CreateIssue($input: IssueCreateInput!) {
    issueCreate(input: $input) {
        success
        issue { id identifier title url }
    }
}
"""

result = linear_query(CREATE_ISSUE, {
    "input": {
        "title": "スキルローダーのエラーハンドリング改善",
        "description": "skills/ ディレクトリが存在しない場合に 500 ではなく空配列を返す",
        "teamId": "TEAM_ID",
        "priority": 2,  # 0=なし 1=緊急 2=高 3=中 4=低
        "labelIds": ["LABEL_BUG_ID"],
    }
})
issue_id = result["data"]["issueCreate"]["issue"]["id"]
```

## イシューの検索・一覧
```python
LIST_ISSUES = """
query TeamIssues($teamId: String!) {
    team(id: $teamId) {
        issues(filter: { state: { type: { neq: "completed" } } }) {
            nodes { id identifier title state { name } assignee { name } priority }
        }
    }
}
"""
issues = linear_query(LIST_ISSUES, {"teamId": "TEAM_ID"})
```

## イシューの更新・クローズ
```python
UPDATE_ISSUE = """
mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
    issueUpdate(id: $id, input: $input) {
        success
        issue { id state { name } }
    }
}
"""

# Done にする
linear_query(UPDATE_ISSUE, {
    "id": issue_id,
    "input": {"stateId": "DONE_STATE_ID"}
})
```

## サイクル（スプリント）管理
```python
GET_CYCLES = """
query { cycles(filter: { isActive: { eq: true } }) {
    nodes { id name startsAt endsAt issues { nodes { title } } }
}}
"""
active_sprints = linear_query(GET_CYCLES)
```

## 注意事項
- `LINEAR_API_KEY` は環境変数で管理する
- チーム ID・ステート ID は事前に API で取得が必要
- ウェブフックで Slack 通知と連携可能

## 検証
Linear のダッシュボードでイシューが作成・更新されれば完了。
