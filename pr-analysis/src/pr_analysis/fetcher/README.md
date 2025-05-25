# Fetcher モジュール

GitHub PRデータを取得するためのモジュールです。

## 主な機能

- PRデータの取得
- 増分更新
- 並列処理
- 様々な取得モード（最新、人気、長期実行中など）

## 主要コンポーネント

### pr_fetcher.py

PRデータを取得するための関数を提供します。

```python
from pr_analysis.fetcher.pr_fetcher import fetch_prs

# PRデータの取得
prs_data = fetch_prs(
    repo_owner="team-mirai",
    repo_name="random",
    limit=100,
    state="all",
    sort_by="updated",
    direction="desc"
)
```

## 依存関係

- pr_analysis.api: GitHub API操作
- pr_analysis.utils: ファイル操作、日付処理
