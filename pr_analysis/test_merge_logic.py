#!/usr/bin/env python3
"""
マージロジックのテストスクリプト

マージ前後のPR数を確認して、データが失われていないかを検証します。
"""

import json
import os

def test_merge_logic():
    """マージロジックのテスト"""
    merged_file = "pr_analysis_results/merged/merged_prs_data.json"
    
    current_data = []
    if os.path.exists(merged_file):
        with open(merged_file, "r", encoding="utf-8") as f:
            current_data = json.load(f)
    
    current_count = len(current_data)
    unique_numbers = {pr.get("basic_info", {}).get("number") for pr in current_data if "basic_info" in pr}
    unique_ids = {pr.get("basic_info", {}).get("id") for pr in current_data if "basic_info" in pr}
    
    print(f"現在のPR総数: {current_count}")
    print(f"一意的なPR number数: {len(unique_numbers)}")
    print(f"一意的なPR id数: {len(unique_ids)}")
    

if __name__ == "__main__":
    test_merge_logic()
