#!/usr/bin/env python3
"""
シンプルなPR取得スクリプト

前回の更新以降に更新されたPRを取得し、タイムスタンプ付きフォルダに保存します。
"""

import os
import json
import datetime
import requests
import time
from pathlib import Path
import concurrent.futures
from tqdm import tqdm

API_BASE_URL = "https://api.github.com"
REPO_OWNER = "team-mirai"
REPO_NAME = "policy"
BASE_OUTPUT_DIR = "pr_analysis_results"

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

def make_github_api_request(url, params=None):
    """GitHubのAPIリクエストを実行する"""
    headers = get_headers()
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def get_pull_requests(last_updated_at=None, state="all"):
    """前回の更新以降に更新されたPull Requestを取得する"""
    all_prs = []
    page = 1
    per_page = 100

    while True:
        url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
        params = {
            "state": state, 
            "per_page": per_page, 
            "page": page,
            "sort": "updated",
            "direction": "desc"
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
            time.sleep(0.5)  # APIレート制限を考慮して少し待機
        except Exception as e:
            print(f"PRリスト取得中にエラーが発生しました (ページ {page}): {e}")
            break

    return all_prs

def get_pr_details(pr_number):
    """PRの詳細情報を取得する"""
    url = f"{API_BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}"
    pr_data = make_github_api_request(url)
    
    pr_details = {
        "basic_info": pr_data,
        "state": pr_data["state"],
        "updated_at": pr_data["updated_at"]
    }
    
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

def load_last_run_info():
    """最後の実行情報を読み込む"""
    last_run_file = Path(BASE_OUTPUT_DIR) / "last_run_info.json"
    
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
    last_run_info = {
        "last_updated_at": last_updated_at.isoformat(),
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
    last_run_file = Path(BASE_OUTPUT_DIR) / "last_run_info.json"
    with open(last_run_file, "w", encoding="utf-8") as f:
        json.dump(last_run_info, f, ensure_ascii=False, indent=2)
    print(f"最後の実行情報を {last_run_file} に保存しました")

def main():
    os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(BASE_OUTPUT_DIR) / timestamp
    output_dir.mkdir(exist_ok=True, parents=True)
    
    last_updated_at = load_last_run_info()
    
    print(f"team-mirai/{REPO_NAME} リポジトリの更新されたPRを収集しています...")
    prs = get_pull_requests(last_updated_at=last_updated_at)
    print(f"{len(prs)}件の更新されたPRを見つけました")
    
    if not prs:
        print("処理対象のPRがありません。処理を終了します。")
        return
    
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
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(valid_prs_data, f, ensure_ascii=False, indent=2)
    print(f"JSONデータを {json_filename} に保存しました")
    
    print(f"処理結果: 成功={len(valid_prs_data)}件")
    print(f"JSON出力: {json_filename}")

if __name__ == "__main__":
    main()
