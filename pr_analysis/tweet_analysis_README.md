# ツイート収集・分析ツール

X.com（旧Twitter）から特定のハッシュタグ（#チームみらい_私の推し提案）を含むツイートを収集し、GitHub URLを抽出・分析するツールです。

## 機能

- X APIを使用して特定のハッシュタグを含むツイートを検索
- ツイートからGitHub URLを抽出（特に team-mirai/policy リポジトリへの言及）
- 収集したデータをJSON形式で保存
- 言及されたURLの集計レポートを生成

## 必要環境

- Python 3.6以上
- tweepy, backoff, requests, tqdm ライブラリ

## インストール

```
pip install tweepy backoff requests tqdm
```

## 環境変数の設定

以下の環境変数を設定してください：

```
export TWITTER_CONSUMER_KEY="your_consumer_key"
export TWITTER_CONSUMER_SECRET="your_consumer_secret"
export TWITTER_ACCESS_TOKEN="your_access_token"
export TWITTER_ACCESS_TOKEN_SECRET="your_access_token_secret"
```

## 使い方

### ツイートの収集とレポート生成（デフォルト）

```
python tweet_analyzer.py
```

### ツイートの収集のみ

```
python tweet_analyzer.py --mode fetch
```

### 既存のJSONファイルからレポート生成のみ

```
python tweet_analyzer.py --mode report --json-file output/tweets_20230101_120000.json
```

### オプション

- `--limit N`: 取得するツイートの最大数を指定（デフォルト: 100）
- `--since YYYY-MM-DD`: この日付以降のツイートを取得
- `--until YYYY-MM-DD`: この日付以前のツイートを取得
- `--output-dir DIR`: 出力ディレクトリを指定（デフォルト: ./output）

## 出力ファイル

1. **JSONデータ**: `output/tweets_YYYYMMDD_HHMMSS.json`
   - 収集したツイートデータとGitHub URL情報を含む

2. **Markdownレポート**: `output/report_YYYYMMDD_HHMMSS.md`
   - ツイート統計情報
   - 最も言及されたURL、PR、Issueのリスト
