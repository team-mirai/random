#!/usr/bin/env python3

import argparse
import concurrent.futures
import datetime
import json
import os
import time
from pathlib import Path

import backoff
import requests
from tqdm import tqdm

API_BASE_URL = "https://api.github.com"
REPO_OWNER = "team-mirai"
REPO_NAME = "policy"


def get_github_token():
    """環境変数からGitHubトークンを取得する"""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        try:
            import subprocess

            result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
            if result.returncode == 0:
                token = result.stdout.strip()
        except Exception as e:
            print(f"gh CLIからトークンを取得できませんでした: {e}")

    return token


def get_headers():
    """APIリクエスト用のヘッダーを取得する"""
    token = get_github_token()
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    return headers


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.RequestException, requests.exceptions.HTTPError),
    max_tries=5,  # 最大5回再試行
    max_time=30,  # 最大30秒
    giveup=lambda e: isinstance(e, requests.exceptions.HTTPError) and e.response.status_code in [401, 403, 404],  # 認証エラーやリソースが存在しない場合は再試行しない
)
def make_github_api_request(url, params=None, headers=None):
    """GitHubのAPIリクエストを実行し、再試行ロジックを適用する"""
    if headers is None:
        headers = get_headers()
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=3,
)
def check_rate_limit():
    """GitHub APIのレート制限状況を確認する"""
    url = f"{API_BASE_URL}/rate_limit"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()

    rate_limit_data = response.json()
    core_rate = rate_limit_data["resources"]["core"]

    remaining = core_rate["remaining"]
    reset_time = datetime.datetime.fromtimestamp(core_rate["reset"])
    now = datetime.datetime.now()

    print(f"API制限: 残り {remaining} リクエスト")
    print(f"制限リセット時間: {reset_time} (あと {(reset_time - now).total_seconds() / 60:.1f} 分)")

    return remaining, reset_time


def get_open_pull_requests(limit=None):
    """オープン状態のPull Requestを取得する"""
    all_prs = []
    page = 1
    per_page = 100

    while True:
        url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
        params = {"state": "open", "per_page": per_page, "page": page}

        try:
            prs = make_github_api_request(url, params=params)
            if not prs:
                break

            all_prs.extend(prs)
            page += 1

            if limit and len(all_prs) >= limit:
                all_prs = all_prs[:limit]
                break

            if page > 1:
                time.sleep(0.5)  # APIレート制限を考慮して少し待機
        except Exception as e:
            print(f"PRリスト取得中にエラーが発生しました (ページ {page}): {e}")
            break

    return all_prs


def get_pr_basic_info(pr_number):
    """PRの基本情報のみを取得する"""
    url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}"
    return make_github_api_request(url)


def get_pr_comments(pr_number):
    """PRのコメントを取得する"""
    url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/issues/{pr_number}/comments"
    return make_github_api_request(url)


def get_pr_review_comments(pr_number):
    """PRのレビューコメントを取得する"""
    url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/comments"
    return make_github_api_request(url)


def get_pr_commits(pr_number):
    """PRのコミット情報を取得する"""
    url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/commits"
    return make_github_api_request(url)


def get_pr_files(pr_number):
    """PRの変更ファイル情報を取得する"""
    url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/files"
    return make_github_api_request(url)


def get_pr_details(
    pr_number,
    include_comments=True,
    include_review_comments=True,
    include_commits=True,
    include_files=True,
):
    """PRの詳細情報を取得する（オプションで取得する情報を選択可能）"""
    pr_data = get_pr_basic_info(pr_number)

    pr_details = {"basic_info": pr_data}

    if include_comments:
        pr_details["comments"] = get_pr_comments(pr_number)

    if include_review_comments:
        pr_details["review_comments"] = get_pr_review_comments(pr_number)

    if include_commits:
        pr_details["commits"] = get_pr_commits(pr_number)

    if include_files:
        pr_details["files"] = get_pr_files(pr_number)

    return pr_details


def process_pr(
    pr,
    include_comments=True,
    include_review_comments=True,
    include_commits=True,
    include_files=True,
):
    """1つのPRを処理する（並列処理用）"""
    try:
        pr_number = pr["number"]
        try:
            return get_pr_details(
                pr_number,
                include_comments=include_comments,
                include_review_comments=include_review_comments,
                include_commits=include_commits,
                include_files=include_files,
            )
        except Exception as e:
            print(f"PR #{pr_number} の処理中にエラーが発生しました: {str(e)[:200]}")
            return None
    except Exception as e:
        print(f"PRのbasic_info取得中にエラーが発生しました: {str(e)[:200]}")
        return None


def save_to_json(data, filename):
    """データをJSON形式で保存する"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSONデータを {filename} に保存しました")


def generate_markdown(prs_data, filename):
    """PRデータからMarkdownレポートを生成する"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# team-mirai/policy リポジトリのPull Request分析\n\n")
        f.write(f"生成日時: {now}\n\n")
        f.write("## オープンなPull Requestの概要\n\n")
        f.write(f"合計: {len(prs_data)}件のオープンPR\n\n")

        f.write("| # | タイトル | 作成者 | 作成日 | 更新日 | コメント数 |\n")
        f.write("|---|---------|--------|--------|--------|------------|\n")

        for pr in prs_data:
            if not pr:  # エラーでNoneが返された場合はスキップ
                continue

            basic = pr["basic_info"]
            pr_number = basic["number"]
            title = basic["title"]
            user = basic["user"]["login"]
            created_at = basic["created_at"].split("T")[0]  # 日付部分のみ
            updated_at = basic["updated_at"].split("T")[0]  # 日付部分のみ

            comments_count = 0
            if "comments" in pr:
                comments_count += len(pr["comments"])
            if "review_comments" in pr:
                comments_count += len(pr["review_comments"])

            f.write(
                f"| #{pr_number} | [{title}]({basic['html_url']}) | {user} | {created_at} | {updated_at} | {comments_count} |\n"
            )

        f.write("\n## 各Pull Requestの詳細\n\n")

        for pr in prs_data:
            if not pr:  # エラーでNoneが返された場合はスキップ
                continue

            basic = pr["basic_info"]
            pr_number = basic["number"]
            title = basic["title"]
            user = basic["user"]["login"]
            created_at = basic["created_at"].replace("T", " ").replace("Z", "")
            updated_at = basic["updated_at"].replace("T", " ").replace("Z", "")

            f.write(f"### #{pr_number}: {title}\n\n")
            f.write(f"- **URL**: {basic['html_url']}\n")
            f.write(f"- **作成者**: {user}\n")
            f.write(f"- **作成日時**: {created_at}\n")
            f.write(f"- **更新日時**: {updated_at}\n")
            f.write(f"- **ブランチ**: {basic['head']['ref']} → {basic['base']['ref']}\n")

            if basic["body"]:
                f.write(f"\n#### 説明\n\n{basic['body']}\n\n")
            else:
                f.write("\n#### 説明\n\n*説明なし*\n\n")

            if "files" in pr and pr["files"]:
                f.write("#### 変更ファイル\n\n")
                for file in pr["files"]:
                    f.write(f"- [{file['filename']}]({file['blob_url']}) ")
                    f.write(f"(追加: {file.get('additions', 0)}, 削除: {file.get('deletions', 0)})\n")

            if "commits" in pr and pr["commits"]:
                f.write(f"\n#### コミット ({len(pr['commits'])}件)\n\n")
                for commit in pr["commits"]:
                    commit_msg = commit["commit"]["message"].split("\n")[0]  # 1行目だけ
                    author = commit["author"]["login"] if commit["author"] else "Unknown"
                    f.write(f"- [{commit_msg}]({commit['html_url']}) by {author}\n")

            if "comments" in pr and pr["comments"]:
                f.write(f"\n#### コメント ({len(pr['comments'])}件)\n\n")
                for comment in pr["comments"]:
                    user = comment["user"]["login"]
                    date = comment["created_at"].replace("T", " ").replace("Z", "")
                    body = comment["body"]
                    f.write(f"**{user}** ({date}):\n\n{body}\n\n---\n\n")

            if "review_comments" in pr and pr["review_comments"]:
                f.write(f"\n#### レビューコメント ({len(pr['review_comments'])}件)\n\n")
                for comment in pr["review_comments"]:
                    user = comment["user"]["login"]
                    date = comment["created_at"].replace("T", " ").replace("Z", "")
                    body = comment["body"]
                    path = comment["path"]
                    position = comment.get("position", "N/A")
                    f.write(f"**{user}** ({date}) on `{path}` at position {position}:\n\n{body}\n\n---\n\n")

            f.write("\n---\n\n")  # PRの区切り

    print(f"Markdownレポートを {filename} に保存しました")


def generate_summary_markdown(prs_data, filename):
    """PRデータから簡易的なサマリーMarkdownを生成する"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    valid_prs = [pr for pr in prs_data if pr]  # Noneを除外

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# team-mirai/policy リポジトリのPull Request概要\n\n")
        f.write(f"生成日時: {now}\n\n")
        f.write("## オープンなPull Requestの統計\n\n")
        f.write(f"合計: {len(valid_prs)}件のオープンPR\n\n")

        non_bot_prs = [pr for pr in valid_prs if not pr["basic_info"]["user"]["login"].endswith("[bot]")]

        f.write("## bot経由でないPR一覧\n\n")
        if non_bot_prs:
            f.write("| # | タイトル | 作成者 | 作成日 | 更新日 |\n")
            f.write("|---|---------|--------|--------|--------|\n")

            for pr in non_bot_prs:
                basic = pr["basic_info"]
                pr_number = basic["number"]
                title = basic["title"]
                user = basic["user"]["login"]
                created_at = basic["created_at"].split("T")[0]
                updated_at = basic["updated_at"].split("T")[0]

                f.write(f"| #{pr_number} | [{title}]({basic['html_url']}) | {user} | {created_at} | {updated_at} |\n")
        else:
            f.write("bot経由でないPRはありません。\n\n")

        if any("files" in pr for pr in valid_prs):
            f.write("\n## 変更対象のファイルごとのPR一覧\n\n")

            file_to_prs = {}
            for pr in valid_prs:
                if "files" in pr and pr["files"]:
                    for file in pr["files"]:
                        filename = file["filename"]
                        if filename not in file_to_prs:
                            file_to_prs[filename] = []
                        file_to_prs[filename].append(pr)

            for filename, prs in sorted(file_to_prs.items()):
                f.write(f"### {filename}\n\n")
                f.write("| # | タイトル | 作成者 | 作成日 | 更新日 |\n")
                f.write("|---|---------|--------|--------|--------|\n")

                for pr in sorted(prs, key=lambda x: x["basic_info"]["created_at"], reverse=True):
                    basic = pr["basic_info"]
                    pr_number = basic["number"]
                    title = basic["title"]
                    user = basic["user"]["login"]
                    created_at = basic["created_at"].split("T")[0]
                    updated_at = basic["updated_at"].split("T")[0]

                    f.write(
                        f"| #{pr_number} | [{title}]({basic['html_url']}) | {user} | {created_at} | {updated_at} |\n"
                    )

                f.write("\n")

    print("サマリーMarkdownを 完了 に保存しました")


def parse_arguments():
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(description="GitHub PRの分析ツール")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="取得するPRの最大数 (デフォルト: 全て)",
    )
    parser.add_argument("--workers", type=int, default=10, help="並列処理のワーカー数 (デフォルト: 10)")
    parser.add_argument("--no-comments", action="store_true", help="コメントを取得しない")
    parser.add_argument("--no-review-comments", action="store_true", help="レビューコメントを取得しない")
    parser.add_argument("--no-commits", action="store_true", help="コミット情報を取得しない")
    parser.add_argument("--no-files", action="store_true", help="変更ファイル情報を取得しない")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="",
        help="出力ディレクトリ (デフォルト: timestamp)",
    )

    return parser.parse_args()


def generate_issues_and_diffs_markdown(prs_data, filename):
    """PRデータからissuesの内容と変更差分を含むMarkdownを生成する"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    valid_prs = [pr for pr in prs_data if pr]  # Noneを除外
    sorted_prs = sorted(valid_prs, key=lambda x: x["basic_info"]["created_at"], reverse=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# team-mirai/policy リポジトリのPull Request - Issues内容と変更差分\n\n")
        f.write(f"生成日時: {now}\n\n")
        f.write("## 全PRのIssues内容と変更差分\n\n")

        for pr in sorted_prs:
            basic = pr["basic_info"]
            pr_number = basic["number"]
            title = basic["title"]
            user = basic["user"]["login"]
            created_at = basic["created_at"].replace("T", " ").replace("Z", "")

            f.write(f"### #{pr_number}: {title}\n\n")
            f.write(f"- **URL**: {basic['html_url']}\n")
            f.write(f"- **作成者**: {user}\n")
            f.write(f"- **作成日時**: {created_at}\n")
            f.write(f"- **ブランチ**: {basic['head']['ref']} → {basic['base']['ref']}\n\n")

            if basic["body"]:
                f.write(f"#### Issue内容\n\n{basic['body']}\n\n")
            else:
                f.write("#### Issue内容\n\n*内容なし*\n\n")

            if "files" in pr and pr["files"]:
                f.write("#### 変更差分\n\n")

                for file in pr["files"]:
                    filename = file["filename"]
                    status = file["status"]  # added, modified, removed
                    additions = file.get("additions", 0)
                    deletions = file.get("deletions", 0)

                    f.write(f"##### {filename} ({status}, +{additions}/-{deletions})\n\n")

                    if "patch" in file:
                        f.write("```diff\n")
                        f.write(file["patch"])
                        f.write("\n```\n\n")
                    else:
                        f.write("*差分情報なし*\n\n")
            else:
                f.write("#### 変更差分\n\n*差分情報なし*\n\n")

            f.write("---\n\n")

    print("Issues内容と変更差分Markdownを 完了 に保存しました")


def generate_file_based_markdown(prs_data, output_dir):
    """編集対象ファイルごとにPRをグループ化し、それぞれのMarkdownを生成する"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    file_to_prs = {}
    valid_prs = [pr for pr in prs_data if pr]  # Noneを除外

    for pr in valid_prs:
        if "files" in pr and pr["files"]:
            for file in pr["files"]:
                filename = file["filename"]
                if filename not in file_to_prs:
                    file_to_prs[filename] = []
                file_to_prs[filename].append((pr, file))

    files_dir = output_dir / "files"
    files_dir.mkdir(exist_ok=True)

    with open(output_dir / "files_index.md", "w", encoding="utf-8") as index_f:
        index_f.write("# team-mirai/policy リポジトリのファイルごとのPull Request\n\n")
        index_f.write(f"生成日時: {now}\n\n")
        index_f.write("## ファイル一覧\n\n")

        for filename, pr_files in sorted(file_to_prs.items()):
            safe_filename = filename.replace("/", "_").replace("\\", "_")
            file_md_path = files_dir / f"{safe_filename}.md"

            pr_count = len(pr_files)
            index_f.write(f"- [{filename}]({file_md_path.relative_to(output_dir)}) ({pr_count}件のPR)\n")

            with open(file_md_path, "w", encoding="utf-8") as f:
                f.write(f"# {filename} に関するPull Request\n\n")
                f.write(f"生成日時: {now}\n\n")
                f.write(f"## このファイルに影響するPull Request ({pr_count}件)\n\n")

                f.write("| # | タイトル | 作成者 | 作成日 | 状態 | 変更 |\n")
                f.write("|---|---------|--------|--------|------|------|\n")

                for pr_data, file_data in sorted(pr_files, key=lambda x: x[0]["basic_info"]["number"]):
                    basic = pr_data["basic_info"]
                    pr_number = basic["number"]
                    title = basic["title"]
                    user = basic["user"]["login"]
                    created_at = basic["created_at"].split("T")[0]
                    status = file_data["status"]
                    changes = f"+{file_data.get('additions', 0)}/-{file_data.get('deletions', 0)}"

                    f.write(
                        f"| #{pr_number} | [{title}]({basic['html_url']}) | {user} | {created_at} | {status} | {changes} |\n"
                    )

                f.write("\n## 各Pull Requestの詳細\n\n")

                for pr_data, file_data in sorted(pr_files, key=lambda x: x[0]["basic_info"]["number"]):
                    basic = pr_data["basic_info"]
                    pr_number = basic["number"]
                    title = basic["title"]
                    user = basic["user"]["login"]
                    created_at = basic["created_at"].replace("T", " ").replace("Z", "")

                    f.write(f"### #{pr_number}: {title}\n\n")
                    f.write(f"- **URL**: {basic['html_url']}\n")
                    f.write(f"- **作成者**: {user}\n")
                    f.write(f"- **作成日時**: {created_at}\n")
                    f.write(f"- **ブランチ**: {basic['head']['ref']} → {basic['base']['ref']}\n\n")

                    if basic["body"]:
                        f.write(f"#### Issue内容\n\n{basic['body']}\n\n")
                    else:
                        f.write("#### Issue内容\n\n*内容なし*\n\n")

                    f.write("#### 変更差分\n\n")
                    filename = file_data["filename"]
                    status = file_data["status"]
                    additions = file_data.get("additions", 0)
                    deletions = file_data.get("deletions", 0)

                    f.write(f"##### {filename} ({status}, +{additions}/-{deletions})\n\n")

                    if "patch" in file_data:
                        f.write("```diff\n")
                        f.write(file_data["patch"])
                        f.write("\n```\n\n")
                    else:
                        f.write("*差分情報なし*\n\n")

                    f.write("---\n\n")

        total_files = len(file_to_prs)
        index_f.write(f"\n\n合計: {total_files}個のファイルが変更されています。\n")

    print(f"ファイルごとのMarkdownを {files_dir} に保存しました")
    print(f"ファイル一覧インデックスを {output_dir / 'files_index.md'} に保存しました")


def main():
    args = parse_arguments()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir or timestamp)
    output_dir.mkdir(exist_ok=True)

    print("team-mirai/policy リポジトリのオープンPRを収集しています...")

    remaining, reset_time = check_rate_limit()
    if remaining < 100:
        print(f"警告: API制限が残り少ないです ({remaining}リクエスト)")
        print(f"制限リセット時間: {reset_time}")
        proceed = input("続行しますか？ (y/n): ")
        if proceed.lower() != "y":
            print("処理を中止します。")
            return

    limit = args.limit if args.limit > 0 else None
    open_prs = get_open_pull_requests(limit)
    print(f"{len(open_prs)}件のオープンPRを見つけました")

    if not open_prs:
        print("オープンなPRがありません。処理を終了します。")
        return

    print(f"{args.workers}個のワーカーで並列処理を開始します...")

    valid_prs_data = []
    error_prs = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(
                process_pr,
                pr,
                include_comments=not args.no_comments,
                include_review_comments=not args.no_review_comments,
                include_commits=not args.no_commits,
                include_files=not args.no_files,
            )
            for pr in open_prs
        ]

        for future in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
            desc="PRの処理",
        ):
            result = future.result()
            if result is not None:  # 有効なPRデータのみを追加
                valid_prs_data.append(result)
            else:
                error_prs.append("不明なPR")  # PR番号が取得できない場合
    
    print(f"処理結果: 成功={len(valid_prs_data)}件, エラー={len(error_prs)}件")
    
    if error_prs:
        print(f"注意: {len(error_prs)}件のPRでエラーが発生しました。これらはJSONに含まれません。")
        error_log_path = output_dir / "error_prs.txt"
        with open(error_log_path, "w", encoding="utf-8") as f:
            for pr_info in error_prs:
                f.write(f"{pr_info}\n")
        print(f"エラーが発生したPRの情報を {error_log_path} に保存しました")

    json_filename = output_dir / "prs_data.json"
    save_to_json(valid_prs_data, json_filename)

    md_filename = output_dir / "prs_report.md"
    generate_markdown(valid_prs_data, md_filename)

    summary_md_filename = output_dir / "prs_summary.md"
    generate_summary_markdown(valid_prs_data, summary_md_filename)

    issues_diffs_md_filename = output_dir / "prs_issues_diffs.md"
    generate_issues_and_diffs_markdown(valid_prs_data, issues_diffs_md_filename)

    generate_file_based_markdown(valid_prs_data, output_dir)

    print("処理が完了しました。")
    print(f"JSON出力: {json_filename}")
    print(f"詳細Markdown出力: {md_filename}")
    print(f"サマリーMarkdown出力: {summary_md_filename}")
    print(f"Issues内容と変更差分出力: {issues_diffs_md_filename}")
    print(f"ファイルごとのMarkdown出力: {output_dir / 'files'} (インデックス: {output_dir / 'files_index.md'})")


if __name__ == "__main__":
    main()
