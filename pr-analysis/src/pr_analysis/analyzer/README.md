# Analyzer モジュール

PRデータを分析するためのモジュールです。

## 主な機能

- コンテンツの分類
- 統計情報の計算
- パターン検出
- 傾向分析

## 主要コンポーネント

### content_classifier.py

PRの内容を分類するための関数を提供します。

```python
from pr_analysis.analyzer.content_classifier import classify_content, is_readme_pr

# コンテンツの分類
category = classify_content(pr_title, pr_body, files)

# READMEに関するPRかどうかの判定
is_readme = is_readme_pr(files)
```

### pr_analyzer.py

PRデータを分析するための関数を提供します。

```python
from pr_analysis.analyzer.pr_analyzer import analyze_prs

# PRデータの分析
analysis_results = analyze_prs(
    prs_data=prs_data,
    repo_owner="team-mirai",
    repo_name="random"
)
```

## 依存関係

- pr_analysis.utils: ファイル操作、日付処理
