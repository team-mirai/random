#!/usr/bin/env python3
"""
PR分析データ更新スクリプト

1. 前回の更新以降に更新されたPRを取得し、タイムスタンプ付きフォルダに保存
2. 取得したデータと既存のmerged_prs_data.jsonをマージして更新

このスクリプトを実行するだけで、merged_prs_data.jsonが最新のデータに更新されます。
"""

import concurrent.futures
import datetime
import json
import os
import time
from pathlib import Path

import requests
from tqdm import tqdm

API_BASE_URL = "https://api.github.com"
REPO_OWNER = "team-mirai"
REPO_NAME = "policy"
BASE_DIR = "pr_analysis_results"
MERGED_DIR = os.path.join(BASE_DIR, "merged")
MERGED_FILE = os.path.join(MERGED_DIR, "merged_prs_data.json")


def get_github_token():
    """環境変数からGitHubトークンを取得する"""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        print("環境変数からGitHubトークンを取得しました")
        return token
    
    token_file = os.path.expanduser("~/.github_token")
    if os.path.exists(token_file):
        try:
            with open(token_file) as f:
                token = f.read().strip()
                if token:
                    print("トークンファイルからGitHubトークンを取得しました")
                    return token
        except Exception as e:
            print(f"トークンファイルからの読み込みに失敗しました: {e}")
    
    try:
        import subprocess
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if result.returncode == 0:
            token = result.stdout.strip()
            if token:
                print("gh CLIからGitHubトークンを取得しました")
                return token
    except Exception as e:
        print(f"gh CLIからトークンを取得できませんでした: {e}")
    
    try:
        print("\n警告: GitHubトークンが見つかりませんでした")
        print("GitHubトークンを入力するか、以下のいずれかの方法でトークンを設定してください:")
        print("1. 環境変数 GITHUB_TOKEN を設定する")
        print("2. ~/.github_token ファイルにトークンを保存する")
        print("3. gh CLIでログインする (gh auth login)")
        token = input("GitHubトークンを入力してください (入力しない場合は空のままEnterを押してください): ").strip()
        
        if token:
            save = input("このトークンを ~/.github_token に保存しますか？ (y/n): ").strip().lower()
            if save == 'y':
                try:
                    with open(token_file, "w") as f:
                        f.write(token)
                    os.chmod(token_file, 0o600)  # ファイルのパーミッションを制限
                    print(f"トークンを {token_file} に保存しました")
                except Exception as e:
                    print(f"トークンの保存に失敗しました: {e}")
    except Exception as e:
        print(f"トークン入力処理中にエラーが発生しました: {e}")
    
    return token


def get_headers():
    """APIリクエスト用のヘッダーを取得する"""
    token = get_github_token()
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
        print(f"認証ヘッダーを設定しました: {headers['Authorization'][:10]}...")
    else:
        print("警告: GitHubトークンが設定されていません。API制限が厳しく適用される可能性があります。")
    return headers


def make_github_api_request(url, params=None, retry_count=3):
    """GitHubのAPIリクエストを実行する"""
    headers = get_headers()
    
    print(f"APIリクエスト: {url}")
    print(f"パラメータ: {params}")
    
    for attempt in range(retry_count):
        try:
            response = requests.get(url, headers=headers, params=params)
            
            print(f"レスポンスステータス: {response.status_code}")
            for key, value in response.headers.items():
                if key.startswith('X-') or key.lower() in ['content-type', 'server']:
                    print(f"ヘッダー {key}: {value}")
            
            rate_limit = response.headers.get('X-RateLimit-Remaining')
            if rate_limit:
                print(f"API残りリクエスト数: {rate_limit}")
            
            if response.status_code == 429:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = max(reset_time - time.time(), 0) + 1
                print(f"APIレート制限に達しました。{wait_time:.0f}秒待機します...")
                time.sleep(wait_time)
                continue
            
            if response.status_code == 403:
                print("403 Forbidden エラーが発生しました。")
                try:
                    error_data = response.json()
                    print(f"エラーメッセージ: {error_data.get('message', 'なし')}")
                    print(f"エラー詳細: {error_data.get('documentation_url', 'なし')}")
                except json.JSONDecodeError:
                    print("エラーレスポンスのJSONパースに失敗しました")
                
                token = get_github_token()
                if token:
                    print(f"トークンの長さ: {len(token)} 文字")
                    print(f"トークンの先頭: {token[:4]}...")
                    print(f"トークンの末尾: ...{token[-4:]}")
                else:
                    print("トークンが設定されていません")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if attempt < retry_count - 1:
                wait_time = 2 ** attempt  # 指数バックオフ
                print(f"APIリクエストエラー: {e}. {wait_time}秒後に再試行します... (試行 {attempt+1}/{retry_count})")
                time.sleep(wait_time)
            else:
                print(f"APIリクエストが失敗しました: {e}")
                raise
    
    raise Exception(f"APIリクエストが{retry_count}回失敗しました: {url}")


def load_json_file(file_path):
    """JSONファイルを読み込む"""
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []


def save_json_file(data, file_path):
    """JSONファイルを保存する"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"データを保存しました: {file_path}")
        return True
    except Exception as e:
        print(f"データ保存中にエラーが発生しました {file_path}: {e}")
        return False


def load_last_run_info():
    """最後の実行情報を読み込む"""
    last_run_file = Path(BASE_DIR) / "last_run_info.json"

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


def save_last_run_info(last_updated_at):
    """最後の実行情報を保存する"""
    last_run_info = {"last_updated_at": last_updated_at.isoformat(), "timestamp": datetime.datetime.now().isoformat()}

    os.makedirs(BASE_DIR, exist_ok=True)
    last_run_file = Path(BASE_DIR) / "last_run_info.json"
    with open(last_run_file, "w", encoding="utf-8") as f:
        json.dump(last_run_info, f, ensure_ascii=False, indent=2)
    print(f"最後の実行情報を保存しました: {last_run_file}")


def get_pull_requests(last_updated_at=None, state="all"):
    """前回の更新以降に更新されたPull Requestを取得する"""
    all_prs = []
    page = 1
    per_page = 100

    while True:
        url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
        params = {"state": state, "per_page": per_page, "page": page, "sort": "updated", "direction": "desc"}

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
            time.sleep(0.5)  # APIレート制限を考慮して少し待機
        except Exception as e:
            print(f"PRリスト取得中にエラーが発生しました (ページ {page}): {e}")
            break

    return all_prs


def get_pr_details(pr_number):
    """PRの詳細情報を取得する"""
    url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}"
    pr_data = make_github_api_request(url)

    pr_details = {"basic_info": pr_data, "state": pr_data["state"], "updated_at": pr_data["updated_at"]}

    try:
        url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/issues/{pr_number}/comments"
        pr_details["comments"] = make_github_api_request(url)
    except Exception:
        pr_details["comments"] = []

    try:
        url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/comments"
        pr_details["review_comments"] = make_github_api_request(url)
    except Exception:
        pr_details["review_comments"] = []

    try:
        url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/files"
        pr_details["files"] = make_github_api_request(url)
    except Exception:
        pr_details["files"] = []

    return pr_details


def process_pr(pr):
    """1つのPRを処理する（並列処理用）"""
    try:
        pr_number = pr["number"]
        return get_pr_details(pr_number)
    except Exception as e:
        print(f"PR #{pr_number} の処理中にエラーが発生しました: {e}")
        return None


def fetch_latest_prs():
    """最新のPRデータを取得する"""
    os.makedirs(BASE_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(BASE_DIR) / timestamp
    output_dir.mkdir(exist_ok=True, parents=True)

    last_updated_at = load_last_run_info()

    print(f"team-mirai/{REPO_NAME} リポジトリの更新されたPRを収集しています...")
    prs = get_pull_requests(last_updated_at=last_updated_at)
    print(f"{len(prs)}件の更新されたPRを見つけました")

    if not prs:
        print("処理対象のPRがありません。")
        return None

    print("並列処理でPR詳細を取得しています...")
    valid_prs_data = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_pr, pr) for pr in prs]

        for future in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
            desc="PRの処理",
        ):
            result = future.result()
            if result is not None:
                valid_prs_data.append(result)

    if valid_prs_data:
        latest_updated_at = max(
            datetime.datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
            for pr in valid_prs_data
            if "updated_at" in pr
        )
        save_last_run_info(latest_updated_at)

    json_filename = output_dir / "prs_data.json"
    save_json_file(valid_prs_data, json_filename)

    print(f"処理結果: 成功={len(valid_prs_data)}件")
    print(f"JSON出力: {json_filename}")

    return {"data": valid_prs_data, "file_path": json_filename}


def merge_with_existing_data(new_prs_data):
    """新しいPRデータと既存のデータをマージする"""
    existing_data = []
    if os.path.exists(MERGED_FILE):
        existing_data = load_json_file(MERGED_FILE)
        print(f"既存の統合ファイルから {len(existing_data)} 件のPRを読み込みました: {MERGED_FILE}")
    
    merged_data = existing_data.copy()
    
    existing_pr_numbers = {pr.get("basic_info", {}).get("number"): i 
                          for i, pr in enumerate(merged_data) 
                          if "basic_info" in pr and pr.get("basic_info", {}).get("number")}
    
    new_count = 0
    update_count = 0
    
    for pr in new_prs_data:
        pr_number = pr.get("basic_info", {}).get("number")
        if not pr_number:
            continue
            
        if pr_number in existing_pr_numbers:
            idx = existing_pr_numbers[pr_number]
            merged_data[idx] = pr
            update_count += 1
        else:
            merged_data.append(pr)
            new_count += 1
    
    os.makedirs(MERGED_DIR, exist_ok=True)
    save_json_file(merged_data, MERGED_FILE)
    
    print(f"データ統合が完了しました: 新規追加={new_count}件, 更新={update_count}件, 合計={len(merged_data)}件")
    
    return len(merged_data)


def main():
    print("PR分析データ更新を開始します...")

    try:
        token = get_github_token()
        if not token:
            print("GitHubトークンが設定されていないため、処理を中止します。")
            return
        
        try:
            rate_limit_url = f"{API_BASE_URL}/rate_limit"
            rate_limit_response = requests.get(rate_limit_url, headers={"Authorization": f"token {token}"})
            if rate_limit_response.status_code == 200:
                rate_limit_data = rate_limit_response.json()
                core_rate = rate_limit_data.get('resources', {}).get('core', {})
                remaining = core_rate.get('remaining', 0)
                limit = core_rate.get('limit', 0)
                reset_time = core_rate.get('reset', 0)
                
                print(f"GitHub API レート制限状況: {remaining}/{limit} リクエスト残り")
                
                if remaining < 10:
                    reset_datetime = datetime.datetime.fromtimestamp(reset_time)
                    reset_datetime_jst = reset_datetime + datetime.timedelta(hours=9)
                    print(f"警告: APIリクエスト数が残り少なくなっています。リセット時間(JST): {reset_datetime_jst}")
                    
                    print(f"レート制限の詳細: 残り {remaining}/{limit} リクエスト")
                    print(f"レート制限のリセット時間(UTC): {reset_datetime}")
                    print(f"レート制限のリセット時間(JST): {reset_datetime_jst}")
                    
                    if remaining == 0:
                        current_time = time.time()
                        wait_time = max(reset_time - current_time, 0) + 5
                        print(f"APIレート制限に達しています。リセットまで {int(wait_time/60)} 分かかります。")
                        
                        print("レート制限に達した理由を調査中...")
                        utc_now = datetime.datetime.now(datetime.timezone.utc)  # noqa: UP017
                        jst_now = utc_now + datetime.timedelta(hours=9)
                        print(f"現在時刻(UTC): {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"現在時刻(JST): {jst_now.strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        if wait_time > 300:  # 5分以上の場合
                            print("処理を中断します。後でもう一度試してください。")
                            return
        except Exception as e:
            print(f"レート制限情報の取得に失敗しました: {e}")
        
        result = fetch_latest_prs()
        
        if result:
            total_prs = merge_with_existing_data(result["data"])
            print(f"PR分析データの更新が完了しました。統合ファイル内のPR総数: {total_prs}")
        else:
            print("新しいPRデータがないため、マージ処理をスキップします。")
            if os.path.exists(MERGED_FILE):
                print(f"既存の統合ファイルは維持されます: {MERGED_FILE}")
            else:
                print(f"統合ファイルが存在しません: {MERGED_FILE}")
    except Exception as e:
        print(f"PR分析データ更新中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
