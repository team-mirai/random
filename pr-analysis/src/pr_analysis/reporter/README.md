# Reporter モジュール

分析結果をさまざまな形式でレポート生成するためのモジュールです。

## 主な機能

- マークダウンレポート生成
- CSVエクスポート
- 統計情報レポート
- ファイルごとのレポート

## 主要コンポーネント

### markdown_generator.py

マークダウン形式のレポートを生成するための関数を提供します。

```python
from pr_analysis.reporter.markdown_generator import (
    generate_markdown,
    generate_summary_markdown,
    generate_issues_and_diffs_markdown,
    generate_file_based_markdown
)

# 詳細なマークダウンレポートの生成
generate_markdown(prs_data, "report.md")

# サマリーマークダウンの生成
generate_summary_markdown(prs_data, "summary.md")

# Issues内容と変更差分マークダウンの生成
generate_issues_and_diffs_markdown(prs_data, "issues_diffs.md")

# ファイルごとのマークダウンの生成
generate_file_based_markdown(prs_data, "files_dir")
```

### csv_generator.py

CSV形式のレポートを生成するための関数を提供します。

```python
from pr_analysis.reporter.csv_generator import (
    generate_csv,
    generate_id_comment_csv,
    generate_stats_csv
)

# 詳細なCSVレポートの生成
generate_csv(prs_data, "report.csv")

# ID-コメントのみのCSVの生成
generate_id_comment_csv(prs_data, "id_comment.csv")

# 統計情報CSVの生成
generate_stats_csv(analysis_results, "stats.csv")
```

## 依存関係

- pr_analysis.utils: ファイル操作、日付処理
