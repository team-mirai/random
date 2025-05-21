#!/usr/bin/env python3
"""
統合されたPRデータを検証するスクリプト
"""

import json
import os
from pathlib import Path


def main():
    repo_root = Path(__file__).parent.parent.absolute()
    merged_file = os.path.join(repo_root, "pr_analysis_results", "merged", "merged_prs_data.json")

    try:
        with open(merged_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        total_prs = len(data)
        pr_numbers = [pr.get("basic_info", {}).get("number", 0) for pr in data if "basic_info" in pr]

        if pr_numbers:
            min_pr = min(pr_numbers)
            max_pr = max(pr_numbers)
            unique_pr_count = len(set(pr_numbers))

            print(f"合計PR数: {total_prs}")
            print(f"PR番号の範囲: {min_pr} ~ {max_pr}")
            print(f"ユニークなPR番号の数: {unique_pr_count}")

            missing_prs = sorted(set(range(1, max_pr + 1)) - set(pr_numbers))
            print(f"欠落しているPR番号の数: {len(missing_prs)}")
            if missing_prs:
                print(f"欠落しているPR番号: {missing_prs}")

    except Exception as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    main()
