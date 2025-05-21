#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import re
from pathlib import Path

import backoff
import tweepy
from tqdm import tqdm

HASHTAG = "チームみらい_私の推し提案"
TARGET_REPO = "team-mirai/policy"


def get_twitter_auth():
    """環境変数からTwitter APIの認証情報を取得する"""
    consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
    consumer_secret = os.environ.get("TWITTER_CONSUMER_SECRET")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

    if not (consumer_key and consumer_secret and access_token and access_token_secret):
        print("Twitter API認証情報が見つかりません。環境変数を設定してください。")
        print("TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET")
        return None

    auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
    return auth


def get_twitter_client():
    """Twitter APIクライアントを取得する"""
    auth = get_twitter_auth()
    if not auth:
        return None

    return tweepy.API(auth)


@backoff.on_exception(
    backoff.expo,
    (tweepy.errors.TooManyRequests, tweepy.errors.TwitterServerError),
    max_tries=5,
    max_time=30,
)
def search_tweets(client, query, max_tweets=100):
    """ハッシュタグを含むツイートを検索する"""
    tweets = []
    try:
        for tweet in tweepy.Cursor(client.search_tweets, q=query, tweet_mode="extended").items(max_tweets):
            tweets.append(tweet._json)
        return tweets
    except tweepy.errors.TweepyException as e:
        print(f"ツイート検索中にエラーが発生しました: {e}")
        return []


def extract_github_urls(tweet_text):
    """ツイートのテキストからGitHub URLを抽出する"""
    github_pattern = r"https?://(?:www\.)?github\.com/[\w\-]+/[\w\-]+(?:/(?:pull|issues)/\d+)?"
    github_urls = re.findall(github_pattern, tweet_text)

    policy_urls = [url for url in github_urls if TARGET_REPO in url]

    return {
        "all_urls": github_urls,
        "policy_urls": policy_urls,
        "pr_urls": [url for url in policy_urls if "/pull/" in url],
        "issue_urls": [url for url in policy_urls if "/issues/" in url],
    }


def process_tweet(tweet):
    """ツイートを処理してGitHub URLを抽出する"""
    tweet_id = tweet["id_str"]
    created_at = tweet["created_at"]
    user_name = tweet["user"]["screen_name"]

    if "full_text" in tweet:
        tweet_text = tweet["full_text"]
    else:
        tweet_text = tweet["text"]

    urls = extract_github_urls(tweet_text)

    return {"id": tweet_id, "created_at": created_at, "user": user_name, "text": tweet_text, "github_urls": urls}


def fetch_tweets(args):
    """ツイートを取得して処理する"""
    print(f"#{HASHTAG} を含むツイートを検索します...")

    client = get_twitter_client()
    if not client:
        print("Twitter APIクライアントの初期化に失敗しました。")
        return None

    query = f"#{HASHTAG}"
    if args.since:
        query += f" since:{args.since}"
    if args.until:
        query += f" until:{args.until}"

    tweets = search_tweets(client, query, args.limit)
    if not tweets:
        print("ツイートが見つかりませんでした。")
        return None

    print(f"{len(tweets)}件のツイートを取得しました。")

    processed_tweets = []
    for tweet in tqdm(tweets, desc="ツイート処理中"):
        processed_tweet = process_tweet(tweet)
        processed_tweets.append(processed_tweet)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"tweets_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(processed_tweets, f, ensure_ascii=False, indent=2)

    print(f"ツイートデータを {json_path} に保存しました。")

    return {"json_path": json_path, "output_dir": output_dir, "tweets_data": processed_tweets}


def generate_report(tweets_data):
    """ツイートデータからレポートを生成する"""
    total_tweets = len(tweets_data)
    total_github_urls = sum(len(t["github_urls"]["all_urls"]) for t in tweets_data)
    total_policy_urls = sum(len(t["github_urls"]["policy_urls"]) for t in tweets_data)
    total_pr_urls = sum(len(t["github_urls"]["pr_urls"]) for t in tweets_data)
    total_issue_urls = sum(len(t["github_urls"]["issue_urls"]) for t in tweets_data)

    url_mentions = {}
    pr_mentions = {}
    issue_mentions = {}

    for tweet in tweets_data:
        for url in tweet["github_urls"]["policy_urls"]:
            url_mentions[url] = url_mentions.get(url, 0) + 1

        for url in tweet["github_urls"]["pr_urls"]:
            pr_id = re.search(r"/pull/(\d+)", url)
            if pr_id:
                pr_id = pr_id.group(1)
                pr_mentions[pr_id] = pr_mentions.get(pr_id, 0) + 1

        for url in tweet["github_urls"]["issue_urls"]:
            issue_id = re.search(r"/issues/(\d+)", url)
            if issue_id:
                issue_id = issue_id.group(1)
                issue_mentions[issue_id] = issue_mentions.get(issue_id, 0) + 1

    report = []
    report.append("# チームみらい推し提案ツイート分析レポート")
    report.append(f"生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("## 概要")
    report.append(f"- 取得ツイート数: {total_tweets}")
    report.append(f"- GitHub URL言及数: {total_github_urls}")
    report.append(f"- team-mirai/policy リポジトリ言及数: {total_policy_urls}")
    report.append(f"- PR言及数: {total_pr_urls}")
    report.append(f"- Issue言及数: {total_issue_urls}")
    report.append("")

    if url_mentions:
        report.append("## 最も言及されたURL")
        sorted_urls = sorted(url_mentions.items(), key=lambda x: x[1], reverse=True)
        for url, count in sorted_urls[:10]:  # 上位10件
            report.append(f"- {url}: {count}回")
        report.append("")

    if pr_mentions:
        report.append("## 最も言及されたPR")
        sorted_prs = sorted(pr_mentions.items(), key=lambda x: x[1], reverse=True)
        for pr_id, count in sorted_prs[:10]:  # 上位10件
            report.append(f"- PR #{pr_id}: {count}回")
        report.append("")

    if issue_mentions:
        report.append("## 最も言及されたIssue")
        sorted_issues = sorted(issue_mentions.items(), key=lambda x: x[1], reverse=True)
        for issue_id, count in sorted_issues[:10]:  # 上位10件
            report.append(f"- Issue #{issue_id}: {count}回")

    return "\n".join(report)


def generate_reports(args, json_path=None, output_dir=None, tweets_data=None):
    """レポートを生成する"""
    if not json_path and args.json_file:
        json_path = args.json_file

    if not output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    if not tweets_data:
        if not json_path:
            print("JSONファイルが指定されていません。")
            return None

        try:
            with open(json_path, encoding="utf-8") as f:
                tweets_data = json.load(f)
        except Exception as e:
            print(f"JSONファイルの読み込み中にエラーが発生しました: {e}")
            return None

    report = generate_report(tweets_data)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"report_{timestamp}.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"レポートを {report_path} に保存しました。")

    return report_path


def parse_arguments():
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(
        description="X.com（旧Twitter）からハッシュタグを含むツイートを取得し、GitHub URLを分析するツール"
    )

    parser.add_argument(
        "--mode",
        choices=["fetch", "report", "both"],
        default="both",
        help="実行モード: fetch=ツイート取得のみ, report=レポート生成のみ, both=両方実行 (デフォルト: both)",
    )

    parser.add_argument("--limit", type=int, default=100, help="取得するツイートの最大数 (デフォルト: 100)")
    parser.add_argument("--since", type=str, help="この日付以降のツイートを取得 (形式: YYYY-MM-DD)")
    parser.add_argument("--until", type=str, help="この日付以前のツイートを取得 (形式: YYYY-MM-DD)")

    parser.add_argument(
        "--json-file", type=str, help="レポート生成に使用するJSONファイルのパス (mode=reportの場合に必須)"
    )

    parser.add_argument("--output-dir", type=str, default="./output", help="出力ディレクトリ (デフォルト: ./output)")

    args = parser.parse_args()

    if args.mode == "report" and not args.json_file:
        parser.error("mode=report の場合、--json-file オプションが必要です。")

    return args


def main():
    """メイン関数"""
    args = parse_arguments()

    if args.mode in ["fetch", "both"]:
        result = fetch_tweets(args)
        if result is None:
            return

        if args.mode == "both":
            generate_reports(
                args, json_path=result["json_path"], output_dir=result["output_dir"], tweets_data=result["tweets_data"]
            )

    elif args.mode == "report":
        generate_reports(args)


if __name__ == "__main__":
    main()
