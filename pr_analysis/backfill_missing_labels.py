#!/usr/bin/env python3
"""
一時的なスクリプト: ラベル情報が不足しているPRのデータを再取得する
   
このスクリプトは、merged_prs_data.jsonから以下のPRを特定して再取得します:
1. top-levelにlabelsキーがないPR
2. labelsキーが空のPR
"""

import concurrent.futures
import json
import os
import time
from pathlib import Path
from tqdm import tqdm
from update_pr_data import (
    get_pr_details, load_json_file, save_json_file, 
    get_github_token, MERGED_FILE, MERGED_DIR
)


def identify_prs_missing_labels(pr_data):
    """ラベル情報が不足しているPRを特定する"""
    missing_label_prs = []
    
    for pr in pr_data:
        if not pr:
            continue
            
        pr_number = pr.get("basic_info", {}).get("number")
        if not pr_number:
            continue
            
        if not pr.get("labels"):
            missing_label_prs.append(pr_number)
    
    return missing_label_prs


def backfill_pr_labels(pr_numbers):
    """不足しているPRのラベル情報を再取得する"""
    print(f"{len(pr_numbers)}件のPRのラベル情報を再取得しています...")
    
    updated_prs = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(get_pr_details, pr_num) for pr_num in pr_numbers]
        
        for future in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
            desc="PRラベル再取得",
        ):
            result = future.result()
            if result is not None:
                updated_prs.append(result)
    
    return updated_prs


def update_merged_data(updated_prs):
    """更新されたPRデータをマージファイルに反映する"""
    existing_data = load_json_file(MERGED_FILE)
    
    existing_pr_map = {
        pr.get("basic_info", {}).get("number"): i 
        for i, pr in enumerate(existing_data) 
        if "basic_info" in pr and pr.get("basic_info", {}).get("number")
    }
    
    update_count = 0
    
    for updated_pr in updated_prs:
        pr_number = updated_pr.get("basic_info", {}).get("number")
        if pr_number in existing_pr_map:
            idx = existing_pr_map[pr_number]
            existing_data[idx] = updated_pr
            update_count += 1
    
    backup_file = f"{MERGED_FILE}.backup_{int(time.time())}"
    save_json_file(existing_data, backup_file)
    print(f"バックアップを作成しました: {backup_file}")
    
    save_json_file(existing_data, MERGED_FILE)
    print(f"{update_count}件のPRデータを更新しました")
    
    return update_count


def main():
    """メイン処理"""
    print("ラベル情報の不足しているPRの再取得を開始します...")
    
    token = get_github_token()
    if not token:
        print("GitHubトークンが設定されていないため、処理を中止します。")
        return
    
    if not os.path.exists(MERGED_FILE):
        print(f"統合ファイルが見つかりません: {MERGED_FILE}")
        return
    
    print(f"統合ファイルを読み込んでいます: {MERGED_FILE}")
    pr_data = load_json_file(MERGED_FILE)
    print(f"{len(pr_data)}件のPRデータを読み込みました")
    
    missing_label_prs = identify_prs_missing_labels(pr_data)
    print(f"ラベル情報が不足している可能性のあるPR: {len(missing_label_prs)}件")
    
    if not missing_label_prs:
        print("ラベル情報が不足しているPRは見つかりませんでした。")
        return
    
    updated_prs = backfill_pr_labels(missing_label_prs)
    
    if updated_prs:
        update_count = update_merged_data(updated_prs)
        print(f"バックフィル処理が完了しました。{update_count}件のPRを更新しました。")
    else:
        print("更新対象のPRデータが取得できませんでした。")


if __name__ == "__main__":
    import time
    main()
