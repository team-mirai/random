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
    giveup=lambda e: isinstance(e, requests.exceptions.HTTPError)
    and e.response.status_code in [401, 403, 404],  # 認証エラーやリソースが存在しない場合は再試行しない
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


def get_pull_requests(limit=None, sort_by="updated", direction="desc", last_updated_at=None, state="open"):
    """Pull Requestを取得する
    
    Args:
        limit: 取得するPRの最大数
        sort_by: ソート基準 ("created", "updated", "popularity", "long-running")
        direction: ソート方向 ("asc" or "desc")
        last_updated_at: 前回実行時の最新更新日時（この日時以降のPRのみ取得）
        state: PRの状態 ("open", "closed", "all")
    """
    all_prs = []
    page = 1
    per_page = 100

    while True:
        url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
        params = {
            "state": state, 
            "per_page": per_page, 
            "page": page,
            "sort": sort_by,
            "direction": direction
        }

        try:
            prs = make_github_api_request(url, params=params)
            if not prs:
                break

            if last_updated_at:
                new_prs = []
                for pr in prs:
                    pr_updated_at = datetime.datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
                    if pr_updated_at <= last_updated_at:
                        print(f"前回処理済みのPR #{pr['number']} に到達しました。処理を終了します。")
                        break
                    new_prs.append(pr)
                
                if len(new_prs) < len(prs):
                    all_prs.extend(new_prs)
                    break
                
                all_prs.extend(new_prs)
            else:
                all_prs.extend(prs)
            
            page += 1

            if limit and len(all_prs) >= limit:
                all_prs = all_prs[:limit]
                break

            if page > 1:
                time.sleep(0.5)  # APIレート制限を考慮して少し待機
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403 and "API rate limit exceeded" in e.response.text:
                print("GitHubのAPIレート制限に達しました。処理を終了します。")
                break
            print(f"PRリスト取得中にエラーが発生しました (ページ {page}): {e}")
            break
        except Exception as e:
            print(f"PRリスト取得中にエラーが発生しました (ページ {page}): {e}")
            break

    return all_prs


def get_pull_requests_sequential(start_id=1, max_id=None, limit=None):
    """PR番号順にPRを取得する（ID1から順に）"""
    all_prs = []
    current_id = start_id
    count = 0
    
    print(f"PR番号 #{start_id} から順にPRを取得します...")
    
    while True:
        try:
            pr = get_pr_by_number(current_id)
            if pr:
                all_prs.append(pr)
                print(f"PR #{current_id} を取得しました")
                count += 1
            else:
                print(f"PR #{current_id} は存在しないためスキップします")
                print(f"PR #{current_id} が存在しないため、これ以上のPRは存在しないと判断して処理を終了します。")
                break
            
            current_id += 1
            
            if max_id and current_id > max_id:
                print(f"最大ID #{max_id} に到達しました。処理を終了します。")
                break
            
            if limit and count >= limit:
                print(f"最大取得数 {limit} に到達しました。処理を終了します。")
                break
            
            # APIレート制限を考慮して少し待機
            time.sleep(0.5)
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403 and "API rate limit exceeded" in e.response.text:
                print("GitHubのAPIレート制限に達しました。処理を終了します。")
                break
            print(f"PR #{current_id} の取得中にエラーが発生しました: {e}")
            current_id += 1  # エラーが発生したら次のIDに進む
        
        except Exception as e:
            print(f"PR #{current_id} の取得中にエラーが発生しました: {e}")
            current_id += 1  # エラーが発生したら次のIDに進む
    
    return all_prs


def get_pull_requests_priority(status_data, limit=None):
    """未取得のPRを優先的に取得する"""
    all_prs = []
    count = 0
    
    none_ids = [int(pr_id) for pr_id, fetch_time in status_data.items() if fetch_time is None]
    none_ids.sort()  # ID順にソート
    
    print(f"{len(none_ids)}件の未取得PRを優先的に取得します...")
    
    for pr_id in none_ids:
        try:
            pr = get_pr_by_number(pr_id)
            if pr:
                all_prs.append(pr)
                print(f"PR #{pr_id} を取得しました")
                count += 1
            else:
                print(f"PR #{pr_id} は存在しないためスキップします")
            
            if limit and count >= limit:
                print(f"最大取得数 {limit} に到達しました。処理を終了します。")
                break
            
            # APIレート制限を考慮して少し待機
            time.sleep(0.5)
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403 and "API rate limit exceeded" in e.response.text:
                print("GitHubのAPIレート制限に達しました。処理を終了します。")
                break
            print(f"PR #{pr_id} の取得中にエラーが発生しました: {e}")
        
        except Exception as e:
            print(f"PR #{pr_id} の取得中にエラーが発生しました: {e}")
    
    if limit and count < limit:
        remaining_limit = limit - count
        print(f"未取得PRの取得が完了しました。残り {remaining_limit} 件を更新日時順で取得します...")
        
        prs = get_pull_requests(limit=remaining_limit, sort_by="updated", direction="desc")
        all_prs.extend(prs)
    
    return all_prs


def get_open_pull_requests(limit=None):
    """オープン状態のPull Requestを取得する（後方互換性のため）"""
    return get_pull_requests(limit=limit, state="open")


def get_pr_basic_info(pr_number):
    """PRの基本情報のみを取得する"""
    url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}"
    return make_github_api_request(url)


def get_pr_by_number(pr_number):
    """PR番号を指定してPRを取得する"""
    try:
        return get_pr_basic_info(pr_number)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"PR #{pr_number} は存在しません")
            return None
        raise


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


def get_pr_labels(pr_number):
    """PRのラベル情報を取得する"""
    url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/issues/{pr_number}/labels"
    return make_github_api_request(url)


def get_pr_details(
    pr_number,
    include_comments=True,
    include_review_comments=True,
    include_commits=True,
    include_files=True,
    include_labels=True,
):
    """PRの詳細情報を取得する（オプションで取得する情報を選択可能）"""
    pr_data = get_pr_basic_info(pr_number)

    pr_details = {
        "basic_info": pr_data,
        "state": pr_data["state"],  # open または closed
        "updated_at": pr_data["updated_at"]  # 更新日時を保存
    }

    if include_labels:
        try:
            pr_details["labels"] = get_pr_labels(pr_number)
        except Exception as e:
            print(f"PR #{pr_number} のラベル取得中にエラーが発生しました: {str(e)[:200]}")
            pr_details["labels"] = []

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
    include_labels=True,
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
                include_labels=include_labels,
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


def save_last_run_info(output_dir, last_updated_at):
    """最後の実行情報を保存する"""
    last_run_info = {
        "last_updated_at": last_updated_at.isoformat(),
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    last_run_file = Path(output_dir) / "last_run_info.json"
    with open(last_run_file, "w", encoding="utf-8") as f:
        json.dump(last_run_info, f, ensure_ascii=False, indent=2)
    print(f"最後の実行情報を {last_run_file} に保存しました")


def load_last_run_info(base_output_dir):
    """最後の実行情報を読み込む"""
    last_run_file = Path(base_output_dir) / "last_run_info.json"
    
    if last_run_file.exists():
        try:
            with open(last_run_file, encoding="utf-8") as f:
                last_run_info = json.load(f)
            
            last_updated_at = datetime.datetime.fromisoformat(last_run_info["last_updated_at"])
            print(f"前回の実行情報を読み込みました: 最終更新日時 = {last_updated_at}")
            return last_updated_at
        except Exception as e:
            print(f"前回の実行情報の読み込み中にエラーが発生しました: {e}")
    
    print("前回の実行情報が見つかりませんでした")
    return None


def load_previous_prs_data(base_output_dir):
    """前回のPRデータを読み込む"""
    dirs = [d for d in Path(base_output_dir).glob("*") if d.is_dir() and d.name[0].isdigit()]
    if not dirs:
        print("前回のPRデータが見つかりませんでした")
        return []
    
    latest_dir = max(dirs, key=lambda d: d.stat().st_mtime)
    json_file = latest_dir / "prs_data.json"
    
    if json_file.exists():
        try:
            with open(json_file, encoding="utf-8") as f:
                prs_data = json.load(f)
            print(f"前回のPRデータを読み込みました: {len(prs_data)}件 ({json_file})")
            return prs_data
        except Exception as e:
            print(f"前回のPRデータの読み込み中にエラーが発生しました: {e}")
    
    print("前回のPRデータが見つかりませんでした")
    return []


def load_pr_status_data(base_output_dir):
    """PRの取得状況データを読み込む"""
    status_file = Path(base_output_dir) / "pr_status.json"
    
    if status_file.exists():
        try:
            with open(status_file, encoding="utf-8") as f:
                status_data = json.load(f)
            print(f"PRの取得状況データを読み込みました: {len(status_data)}件のPR")
            return status_data
        except Exception as e:
            print(f"PRの取得状況データの読み込み中にエラーが発生しました: {e}")
    
    print("PRの取得状況データが見つかりませんでした")
    return {}


def save_pr_status_data(base_output_dir, status_data):
    """PRの取得状況データを保存する"""
    status_file = Path(base_output_dir) / "pr_status.json"
    
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)
    print(f"PRの取得状況データを {status_file} に保存しました: {len(status_data)}件")


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
        "--mode",
        type=str,
        choices=["fetch", "report", "both"],
        default="both",
        help="実行モード: fetch=PRデータのみ取得, report=既存JSONからレポート生成, both=両方実行 (デフォルト: both)",
    )
    
    fetch_group = parser.add_argument_group("PR取得オプション (--mode fetch または both の場合)")
    fetch_group.add_argument(
        "--limit",
        type=int,
        default=0,
        help="取得するPRの最大数 (デフォルト: 全て)",
    )
    fetch_group.add_argument("--workers", type=int, default=10, help="並列処理のワーカー数 (デフォルト: 10)")
    fetch_group.add_argument("--no-comments", action="store_true", help="コメントを取得しない")
    fetch_group.add_argument("--no-review-comments", action="store_true", help="レビューコメントを取得しない")
    fetch_group.add_argument("--no-commits", action="store_true", help="コミット情報を取得しない")
    fetch_group.add_argument("--no-files", action="store_true", help="変更ファイル情報を取得しない")
    fetch_group.add_argument(
        "--ignore-last-run",
        action="store_true",
        help="前回の実行情報を無視して全PRを取得する",
    )
    fetch_group.add_argument(
        "--open-only",
        action="store_true",
        help="オープン状態のPRのみを取得する",
    )
    fetch_group.add_argument(
        "--fetch-mode",
        type=str,
        choices=["updated", "sequential", "priority"],
        default="updated",
        help="PRの取得モード: updated=更新日時順, sequential=ID順, priority=未取得優先 (デフォルト: updated)",
    )
    fetch_group.add_argument(
        "--start-id",
        type=int,
        default=1,
        help="ID順取得時の開始ID (デフォルト: 1)",
    )
    fetch_group.add_argument(
        "--max-id",
        type=int,
        default=0,
        help="ID順取得時の最大ID (デフォルト: 0=制限なし)",
    )
    
    report_group = parser.add_argument_group("レポート生成オプション (--mode report または both の場合)")
    report_group.add_argument(
        "--filter-state",
        type=str,
        choices=["open", "closed"],
        help="指定した状態のPRのみをレポートに含める",
    )
    report_group.add_argument(
        "--input-json",
        type=str,
        help="レポート生成に使用するJSONファイルのパス (--mode report の場合に必須)",
    )
    report_group.add_argument(
        "--classify-readme",
        action="store_true",
        help="README対象のPRを分類する"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="",
        help="出力ディレクトリ (デフォルト: timestamp)",
    )
    parser.add_argument(
        "--base-output-dir",
        type=str,
        default="pr_analysis_results",
        help="基本出力ディレクトリ (デフォルト: pr_analysis_results)",
    )

    args = parser.parse_args()
    
    if args.mode == "report" and not args.input_json:
        parser.error("--mode report の場合、--input-json が必須です")
        
    return args


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


def fetch_pr_data(args):
    """
    GitHubからPRデータを取得してJSONに保存する関数
    この関数はGitHub APIを消費する
    """
    base_output_dir = Path(args.base_output_dir)
    base_output_dir.mkdir(exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir or f"{base_output_dir}/{timestamp}")
    output_dir.mkdir(exist_ok=True, parents=True)

    print(f"team-mirai/{REPO_NAME} リポジトリのPRを収集しています...")

    remaining, reset_time = check_rate_limit()
    if remaining < 100:
        print(f"警告: API制限が残り少ないです ({remaining}リクエスト)")
        print(f"制限リセット時間: {reset_time}")
        proceed = input("続行しますか？ (y/n): ")
        if proceed.lower() != "y":
            print("処理を中止します。")
            return None

    status_data = {}
    if not args.ignore_last_run:
        status_data = load_pr_status_data(base_output_dir)

    last_updated_at = None
    if not args.ignore_last_run:
        last_updated_at = load_last_run_info(base_output_dir)

    limit = args.limit if args.limit > 0 else None
    pr_state = "open" if args.open_only else "all"
    
    if args.fetch_mode == "sequential":
        prs = get_pull_requests_sequential(
            start_id=args.start_id,
            max_id=args.max_id if args.max_id > 0 else None,
            limit=limit
        )
    elif args.fetch_mode == "priority":
        prs = get_pull_requests_priority(
            status_data=status_data,
            limit=limit
        )
    else:  # "updated"モード（デフォルト）
        prs = get_pull_requests(
            limit=limit, 
            sort_by="updated", 
            direction="desc", 
            last_updated_at=last_updated_at,
            state=pr_state
        )
    
    print(f"{len(prs)}件のPRを見つけました")

    if not prs:
        print("処理対象のPRがありません。処理を終了します。")
        return None

    previous_prs_data = []
    if not args.ignore_last_run and last_updated_at:
        previous_prs_data = load_previous_prs_data(base_output_dir)

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
                include_labels=True,  # ラベル情報は常に取得
            )
            for pr in prs
        ]

        for future in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
            desc="PRの処理",
        ):
            result = future.result()
            if result is not None:  # 有効なPRデータのみを追加
                valid_prs_data.append(result)
                pr_number = str(result["basic_info"]["number"])
                pr_updated_at = result["updated_at"]
                status_data[pr_number] = pr_updated_at
            else:
                error_prs.append("不明なPR")  # PR番号が取得できない場合

    if previous_prs_data:
        current_pr_ids = {pr["basic_info"]["number"] for pr in valid_prs_data}
        
        for pr in previous_prs_data:
            if pr["basic_info"]["number"] not in current_pr_ids:
                valid_prs_data.append(pr)
        
        print(f"前回のデータと統合: 合計{len(valid_prs_data)}件のPR")

    print(f"処理結果: 成功={len(valid_prs_data)}件, エラー={len(error_prs)}件")

    if error_prs:
        print(f"注意: {len(error_prs)}件のPRでエラーが発生しました。これらはJSONに含まれません。")
        error_log_path = output_dir / "error_prs.txt"
        with open(error_log_path, "w", encoding="utf-8") as f:
            for pr_info in error_prs:
                f.write(f"{pr_info}\n")
        print(f"エラーが発生したPRの情報を {error_log_path} に保存しました")

    if valid_prs_data:
        latest_updated_at = max(
            datetime.datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
            for pr in valid_prs_data
            if "updated_at" in pr
        )
        save_last_run_info(base_output_dir, latest_updated_at)
        
        save_pr_status_data(base_output_dir, status_data)

    json_filename = output_dir / "prs_data.json"
    save_to_json(valid_prs_data, json_filename)
    
    print("PRデータの取得と保存が完了しました。")
    print(f"JSON出力: {json_filename}")
    
    return {
        "json_path": json_filename,
        "output_dir": output_dir,
        "prs_data": valid_prs_data
    }


def generate_reports(args, json_path=None, output_dir=None, prs_data=None):
    """
    JSONデータからMarkdownレポートを生成する関数
    この関数はGitHub APIを消費しない
    """
    if prs_data is None:
        if json_path is None:
            json_path = args.input_json
        
        print(f"JSONファイル {json_path} からデータを読み込んでいます...")
        with open(json_path, encoding="utf-8") as f:
            prs_data = json.load(f)
        
        print(f"{len(prs_data)}件のPRデータを読み込みました")
    
    if output_dir is None:
        base_output_dir = Path(args.base_output_dir)
        base_output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(args.output_dir or f"{base_output_dir}/{timestamp}_report")
        output_dir.mkdir(exist_ok=True, parents=True)
    
    filtered_prs_data = prs_data
    if args.filter_state:
        filtered_prs_data = [pr for pr in prs_data if pr["state"] == args.filter_state]
        print(f"状態 '{args.filter_state}' でフィルタリング: {len(filtered_prs_data)}/{len(prs_data)}件")
    
    if args.classify_readme:
        from content_classifier import ContentClassifier
        classifier = ContentClassifier()
        
        readme_prs = []
        for pr in filtered_prs_data:
            is_readme_pr = False
            if "files" in pr and pr["files"]:
                for file in pr["files"]:
                    if file["filename"].lower() == "readme.md":
                        is_readme_pr = True
                        break
            
            if is_readme_pr:
                readme_prs.append(pr)
        
        print(f"README対象PRを検出: {len(readme_prs)}件")
        
        if readme_prs:
            classified_dir = output_dir / "classified"
            classified_dir.mkdir(exist_ok=True)
            
            with open(classified_dir / "classification_summary.md", "w", encoding="utf-8") as summary_f:
                summary_f.write("# README対象PRの分類結果\n\n")
                summary_f.write("| PR番号 | タイトル | 分類カテゴリ | 信頼度 | 説明 |\n")
                summary_f.write("|--------|----------|--------------|--------|------|\n")
                
                categories = {}
                
                for pr in tqdm(readme_prs, desc="README対象PRの分類"):
                    classification = classifier.classify_content(pr)
                    category = classification.get("category", "分類不能")
                    confidence = classification.get("confidence", 0.0)
                    explanation = classification.get("explanation", "")
                    
                    basic = pr["basic_info"]
                    pr_number = basic["number"]
                    title = basic["title"]
                    
                    summary_f.write(f"| #{pr_number} | {title} | {category} | {confidence:.2f} | {explanation} |\n")
                    
                    if category not in categories:
                        categories[category] = []
                    categories[category].append((pr, classification))
                
                summary_f.write(f"\n## 分類統計\n\n")
                for category, prs in sorted(categories.items()):
                    summary_f.write(f"- {category}: {len(prs)}件\n")
            
            for category, prs in categories.items():
                safe_category = category.replace("/", "_").replace("\\", "_")
                category_file = classified_dir / f"{safe_category}.md"
                
                with open(category_file, "w", encoding="utf-8") as f:
                    f.write(f"# カテゴリ: {category} の Pull Requests\n\n")
                    
                    for pr, classification in prs:
                        basic = pr["basic_info"]
                        pr_number = basic["number"]
                        title = basic["title"]
                        confidence = classification.get("confidence", 0.0)
                        explanation = classification.get("explanation", "")
                        
                        f.write(f"## #{pr_number}: {title}\n\n")
                        f.write(f"- 信頼度: {confidence:.2f}\n")
                        f.write(f"- 分類理由: {explanation}\n\n")
                        
                        if basic["body"]:
                            f.write(f"### PR内容\n\n{basic['body']}\n\n")
                        
                        f.write("---\n\n")
            
            print(f"README対象PRの分類結果を {classified_dir} に保存しました")
    
    md_filename = output_dir / "prs_report.md"
    generate_markdown(filtered_prs_data, md_filename)

    summary_md_filename = output_dir / "prs_summary.md"
    generate_summary_markdown(filtered_prs_data, summary_md_filename)

    issues_diffs_md_filename = output_dir / "prs_issues_diffs.md"
    generate_issues_and_diffs_markdown(filtered_prs_data, issues_diffs_md_filename)

    generate_file_based_markdown(filtered_prs_data, output_dir)

    print("レポート生成が完了しました。")
    print(f"詳細Markdown出力: {md_filename}")
    print(f"サマリーMarkdown出力: {summary_md_filename}")
    print(f"Issues内容と変更差分出力: {issues_diffs_md_filename}")
    print(f"ファイルごとのMarkdown出力: {output_dir / 'files'} (インデックス: {output_dir / 'files_index.md'})")
    
    if args.classify_readme:
        # readme_prsとclassified_dirが定義されている場合のみ出力
        classification_summary_path = None
        if 'readme_prs' in locals() and readme_prs:
            if 'classified_dir' in locals():
                classification_summary_path = classified_dir / 'classification_summary.md'
        
        if classification_summary_path:
            print(f"README対象PR分類結果: {classification_summary_path}")


def main():
    """
    メイン関数
    モードに応じて処理を分岐する
    """
    args = parse_arguments()
    
    if args.mode in ["fetch", "both"]:
        result = fetch_pr_data(args)
        if result is None:
            return
        
        if args.mode == "both":
            generate_reports(args, 
                            json_path=result["json_path"], 
                            output_dir=result["output_dir"], 
                            prs_data=result["prs_data"])
    
    elif args.mode == "report":
        generate_reports(args)


if __name__ == "__main__":
    main()
