#!/usr/bin/env python3
"""
シンプルなPRデータ統合スクリプト

最新のPRデータと既存のmerged_prs_data.jsonを統合し、新しいmerged_prs_data.jsonを作成します。
"""

import glob
import json
import os

BASE_DIR = "pr_analysis_results"
MERGED_DIR = os.path.join(BASE_DIR, "merged")
MERGED_FILE = os.path.join(MERGED_DIR, "merged_prs_data.json")

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
        print(f"Saved merged data to {file_path}")
        return True
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")
        return False

def find_latest_data_dir():
    """最新のデータディレクトリを見つける"""
    dirs = [d for d in glob.glob(os.path.join(BASE_DIR, "*")) if os.path.isdir(d) and not d.endswith("merged")]
    if not dirs:
        print("データディレクトリが見つかりませんでした")
        return None
    
    latest_dir = sorted(dirs)[-1]
    return latest_dir

def merge_pr_data():
    """PRデータを統合する"""
    latest_dir = find_latest_data_dir()
    if not latest_dir:
        return 0
    
    latest_data_file = os.path.join(latest_dir, "prs_data.json")
    if not os.path.exists(latest_data_file):
        print(f"最新のデータファイルが見つかりませんでした: {latest_data_file}")
        return 0
    
    latest_prs = load_json_file(latest_data_file)
    print(f"最新のデータファイルから {len(latest_prs)} 件のPRを読み込みました: {latest_data_file}")
    
    existing_data = []
    if os.path.exists(MERGED_FILE):
        existing_data = load_json_file(MERGED_FILE)
        print(f"既存の統合ファイルから {len(existing_data)} 件のPRを読み込みました: {MERGED_FILE}")
    
    existing_pr_map = {pr.get("basic_info", {}).get("number"): pr for pr in existing_data if "basic_info" in pr}
    
    new_count = 0
    update_count = 0
    
    for pr in latest_prs:
        pr_number = pr.get("basic_info", {}).get("number")
        if not pr_number:
            continue
            
        if pr_number in existing_pr_map:
            existing_pr_map[pr_number] = pr
            update_count += 1
        else:
            existing_pr_map[pr_number] = pr
            new_count += 1
    
    merged_data = list(existing_pr_map.values())
    
    if save_json_file(merged_data, MERGED_FILE):
        print(f"データ統合が完了しました: 新規追加={new_count}件, 更新={update_count}件, 合計={len(merged_data)}件")
    
    return len(merged_data)

def main():
    print("PRデータの統合を開始します...")
    total_prs = merge_pr_data()
    print(f"PRデータの統合が完了しました。統合ファイル内のPR総数: {total_prs}")

if __name__ == "__main__":
    main()
