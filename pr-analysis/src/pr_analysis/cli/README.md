# CLI モジュール

コマンドラインインターフェースを提供するモジュールです。

## 主な機能

- コマンドライン引数の解析
- 各機能へのアクセス
- ヘルプメッセージの表示
- エラーハンドリング

## 主要コンポーネント

### fetcher.py

PRデータ取得のためのCLIを提供します。

```bash
python -m pr_analysis.cli.fetcher --owner team-mirai --repo random --output-dir ./data
```

### analyzer.py

PRデータ分析のためのCLIを提供します。

```bash
python -m pr_analysis.cli.analyzer --input ./data/prs_data.json --owner team-mirai --repo random --output ./data/analysis_results.json
```

### reporter.py

レポート生成のためのCLIを提供します。

```bash
python -m pr_analysis.cli.reporter --input ./data/prs_data.json --format markdown --output ./reports/report.md
```

## 依存関係

- argparse: コマンドライン引数の解析
- pr_analysis.fetcher: PRデータ取得
- pr_analysis.analyzer: PRデータ分析
- pr_analysis.reporter: レポート生成
