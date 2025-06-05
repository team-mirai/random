# API モジュール

GitHub APIとの通信を担当するモジュールです。

## 主な機能

- GitHub APIへの認証
- レート制限の処理
- APIエンドポイントへのアクセス
- エラーハンドリング

## 主要コンポーネント

### github.py

GitHub APIとの通信を行うクラスと関数を提供します。

```python
from pr_analysis.api.github import GitHubClient

# クライアントの初期化
client = GitHubClient(token="your_github_token")

# PRデータの取得
pr_data = client.get_pull_request(owner="team-mirai", repo="random", pr_number=123)
```

## 依存関係

- requests: HTTPリクエスト
- backoff: レート制限時の再試行
