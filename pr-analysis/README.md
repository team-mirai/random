# PR分析ツール

GitHub Pull Requestデータを取得、分析、レポート生成するためのモジュール化されたツールセットです。

## 機能

- GitHub APIを使用したPRデータの取得
- PRデータの分析と分類
- 様々な形式（マークダウン、CSV）でのレポート生成
- コマンドラインインターフェース

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/team-mirai/random.git
cd random/pr-analysis

# 依存関係のインストール
pip install -e .
```

## 使用方法

### コマンドラインから

#### PRデータの取得

```bash
python -m pr_analysis.cli.fetcher --owner <リポジトリオーナー> --repo <リポジトリ名> --output-dir <出力ディレクトリ>
```

オプション:
- `--limit`: 取得するPRの最大数
- `--state`: PRの状態（open, closed, all）
- `--sort-by`: ソート基準（created, updated, popularity, long-running）
- `--direction`: ソート方向（asc, desc）
- `--no-comments`: コメントを含めない
- `--no-review-comments`: レビューコメントを含めない
- `--no-commits`: コミット情報を含めない
- `--no-files`: 変更ファイル情報を含めない
- `--no-labels`: ラベル情報を含めない

#### PRデータの分析

```bash
python -m pr_analysis.cli.analyzer --input <入力JSONファイル> --owner <リポジトリオーナー> --repo <リポジトリ名> --output <出力ファイル>
```

#### レポート生成

```bash
python -m pr_analysis.cli.reporter --input <入力JSONファイル> --format <レポート形式> --output <出力ファイル>
```

レポート形式:
- `markdown`: 詳細なマークダウンレポート
- `summary`: サマリーマークダウン
- `issues`: Issues内容と変更差分マークダウン
- `files`: ファイルごとのマークダウン
- `csv`: CSV形式
- `id_comment`: ID-コメントのみのCSV
- `stats`: 統計情報CSV

### Pythonコードから

```python
from pr_analysis.fetcher import fetch_prs
from pr_analysis.analyzer import analyze_prs
from pr_analysis.reporter import generate_markdown

# PRデータの取得
prs_data = fetch_prs(
    repo_owner="owner",
    repo_name="repo",
    limit=100,
    state="all"
)

# PRデータの分析
analyzed_data = analyze_prs(
    prs_data=prs_data,
    repo_owner="owner",
    repo_name="repo"
)

# レポート生成
generate_markdown(analyzed_data, "report.md")
```

## モジュール構造

```
pr-analysis/
├── src/
│   ├── pr_analysis/
│   │   ├── __init__.py
│   │   ├── api/         # GitHub API操作
│   │   ├── fetcher/     # PRデータ取得
│   │   ├── analyzer/    # データ分析
│   │   ├── reporter/    # レポート生成
│   │   ├── cli/         # コマンドラインインターフェース
│   │   └── utils/       # 共通ユーティリティ
├── tests/               # テストコード
├── pyproject.toml       # プロジェクト設定
└── README.md            # ドキュメント
```

## 各モジュールの説明

### api

GitHub APIとの通信を担当するモジュールです。認証、レート制限の処理、APIエンドポイントへのアクセスを提供します。

### fetcher

GitHub PRデータを取得するためのモジュールです。増分更新、並列処理、様々な取得モードをサポートしています。

### analyzer

PRデータを分析するためのモジュールです。コンテンツの分類、統計情報の計算、パターン検出などの機能を提供します。

### reporter

分析結果をさまざまな形式（マークダウン、CSV）でレポート生成するためのモジュールです。

### cli

コマンドラインインターフェースを提供するモジュールです。各機能へのアクセスを簡素化します。

### utils

ファイル操作、日付処理などの共通ユーティリティ関数を提供するモジュールです。

## 開発

### 環境設定

```bash
# 開発用依存関係をインストール
pip install -e ".[dev]"

# テストを実行
pytest
```

## 貢献

1. リポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを作成

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
