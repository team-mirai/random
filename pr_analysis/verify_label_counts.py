#!/usr/bin/env python3
"""
ラベル数の検証スクリプト
"""

import sys

sys.path.append('/home/ubuntu/repos/random/pr_analysis')
from generate_label_markdown import group_prs_by_label
from update_pr_data import MERGED_FILE, load_json_file


def main():
    print(f"データを読み込んでいます: {MERGED_FILE}")
    pr_data = load_json_file(MERGED_FILE)
    print(f"読み込み完了: {len(pr_data)}件のPR")
    
    grouped = group_prs_by_label(pr_data)
    
    keizai_count = len(grouped.get('経済財政', []))
    print(f"\n経済財政ラベルのPR数: {keizai_count}")
    
    print(f"\n全ラベル数: {len(grouped)}")
    print("\nトップ10ラベル:")
    sorted_labels = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (label, prs) in enumerate(sorted_labels[:10], 1):
        print(f"{i}. {label}: {len(prs)}件")

if __name__ == "__main__":
    main()
