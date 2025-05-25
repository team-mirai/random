# PR Analysis Tool

GitHub Pull Requestを分析するためのツールです。PRの内容を取得し、分析レポートを生成します。

## 機能

- GitHub APIを使用したPRデータの取得
- PRデータの分析と統計情報の生成
- マークダウン形式のレポート生成
- CSVへのデータエクスポート
- コンテンツの自動分類

## インストール

```bash
pip install pr-analysis
```

または、ソースからインストール：

```bash
git clone https://github.com/team-mirai/pr-analysis.git
cd pr-analysis
pip install -e .
```

## 使用方法

### コマンドライン

```bash
# PRデータを取得
pr-fetcher --owner team-mirai --repo policy --output prs_data.json

# PRデータを分析してレポートを生成
pr-analyzer --input prs_data.json --output report.md

# CSVにエクスポート
pr-reporter --input prs_data.json --format csv --output prs_data.csv
```

### Pythonコード

```python
from pr_analysis.fetcher import fetch_prs
from pr_analysis.analyzer import analyze_prs
from pr_analysis.reporter import generate_report

# PRデータを取得
prs_data = fetch_prs(owner="team-mirai", repo="policy")

# PRデータを分析
analysis_results = analyze_prs(prs_data)

# レポートを生成
generate_report(analysis_results, output_format="markdown", output_file="report.md")
```

## 開発

### 環境設定

```bash
# 開発用依存関係をインストール
pip install -e ".[dev]"

# テストを実行
pytest
```

### プロジェクト構造

```
pr-analysis/
├── src/
│   ├── pr_analysis/
│   │   ├── __init__.py
│   │   ├── api/         # GitHub API操作
│   │   ├── fetcher/     # PRデータ取得
│   │   ├── analyzer/    # データ分析
│   │   ├── reporter/    # レポート生成
│   │   └── utils/       # 共通ユーティリティ
├── tests/               # テストコード
├── scripts/             # コマンドラインスクリプト
├── docs/                # ドキュメント
└── examples/            # 使用例
```

## ライセンス

MIT
