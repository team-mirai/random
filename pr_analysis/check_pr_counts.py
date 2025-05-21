#!/usr/bin/env python3
"""
PRデータファイルの数を確認するスクリプト
"""

import json
import os
import glob
from pathlib import Path

def count_prs_in_file(file_path):
    """ファイル内のPR数を数える"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return len(data)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return 0

def main():
    repo_root = Path(__file__).parent.parent.absolute()
    
    dirs_to_check = ["20250521_021502", "20250521_034352", "20250521_034935", "20250521_094649"]
    total_count = 0
    
    for dir_name in dirs_to_check:
        file_path = os.path.join(repo_root, "pr_analysis_results", dir_name, "prs_data.json")
        count = count_prs_in_file(file_path)
        print(f"{dir_name}: {count} PRs")
        total_count += count
    
    print(f"合計: {total_count} PRs")
    
    merged_file = os.path.join(repo_root, "pr_analysis_results", "merged", "merged_prs_data.json")
    merged_count = count_prs_in_file(merged_file)
    print(f"統合ファイル: {merged_count} PRs")
    
    if merged_count > 0:
        with open(merged_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            pr_numbers = [pr.get("basic_info", {}).get("number", 0) for pr in data if "basic_info" in pr]
            if pr_numbers:
                print(f"PR番号の範囲: {min(pr_numbers)} ~ {max(pr_numbers)}")
                print(f"ユニークなPR番号の数: {len(set(pr_numbers))}")
                
                missing_prs = []
                for i in range(1, max(pr_numbers) + 1):
                    if i not in pr_numbers:
                        missing_prs.append(i)
                if missing_prs:
                    print(f"欠落しているPR番号の数: {len(missing_prs)}")
                    if len(missing_prs) < 20:
                        print(f"欠落しているPR番号: {missing_prs}")
                    else:
                        print(f"欠落しているPR番号の一部: {missing_prs[:20]}...")

if __name__ == "__main__":
    main()
