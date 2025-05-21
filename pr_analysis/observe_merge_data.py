#!/usr/bin/env python3
"""
merge_with_existing_data関数の具体的な数値を観察するための使い捨てスクリプト
"""

import json
import os

# 定数定義
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


def observe_merge_data():
    """merge_with_existing_dataの動作を観察する"""
    # 既存データの読み込み
    existing_data = []
    if os.path.exists(MERGED_FILE):
        existing_data = load_json_file(MERGED_FILE)
        print(f"既存の統合ファイルから {len(existing_data)} 件のPRを読み込みました: {MERGED_FILE}")
    else:
        print(f"統合ファイルが存在しません: {MERGED_FILE}")
        return

    # 既存PRマップの作成と分析
    existing_pr_map = {pr.get("basic_info", {}).get("number"): pr for pr in existing_data if "basic_info" in pr}
    print(f"\n既存PRマップのキー数: {len(existing_pr_map)}")

    # PRの番号一覧を表示
    pr_numbers = list(existing_pr_map.keys())
    pr_numbers.sort()  # 番号順にソート
    print(f"\nPR番号一覧 (先頭10件): {pr_numbers[:10]}")

    # 各PRの基本情報を表示
    print("\n各PRの基本情報サンプル (先頭3件):")
    for i, pr_number in enumerate(pr_numbers[:3]):
        pr = existing_pr_map[pr_number]
        basic_info = pr.get("basic_info", {})
        print(f"\n--- PR #{pr_number} ---")
        print(f"タイトル: {basic_info.get('title', 'N/A')}")
        print(f"状態: {basic_info.get('state', 'N/A')}")
        print(f"作成日: {basic_info.get('created_at', 'N/A')}")
        print(f"更新日: {basic_info.get('updated_at', 'N/A')}")

        # PRの構造を表示
        print("\nPRオブジェクトのキー:")
        print(list(pr.keys()))

        # コメント数などの情報
        comments = pr.get("comments", [])
        review_comments = pr.get("review_comments", [])
        files = pr.get("files", [])
        print(f"コメント数: {len(comments)}")
        print(f"レビューコメント数: {len(review_comments)}")
        print(f"変更ファイル数: {len(files)}")

    # PRの状態別カウント
    state_counts = {}
    for pr in existing_data:
        state = pr.get("state", "unknown")
        state_counts[state] = state_counts.get(state, 0) + 1

    print("\nPRの状態別カウント:")
    for state, count in state_counts.items():
        print(f"  {state}: {count}件")

    # 更新日時の分布
    print("\n更新日時の分布:")
    try:
        import collections
        from datetime import datetime

        # 月ごとの更新数をカウント
        month_counts = collections.Counter()
        for pr in existing_data:
            updated_at = pr.get("updated_at")
            if updated_at:
                # "Z"を"+00:00"に置き換えてISO形式に変換
                if "Z" in updated_at:
                    updated_at = updated_at.replace("Z", "+00:00")
                date = datetime.fromisoformat(updated_at)
                month_key = f"{date.year}-{date.month:02d}"
                month_counts[month_key] += 1

        # 月ごとの更新数を表示
        for month, count in sorted(month_counts.items()):
            print(f"  {month}: {count}件")
    except Exception as e:
        print(f"更新日時の分析中にエラーが発生しました: {e}")

    # マージ処理のシミュレーション
    print("\nマージ処理のシミュレーション:")
    # サンプルの新しいPRデータを作成
    sample_new_pr = {
        "basic_info": {
            "number": 9999,  # 存在しない番号
            "title": "サンプルPR",
            "state": "open",
            "created_at": "2025-05-21T00:00:00Z",
            "updated_at": "2025-05-21T00:00:00Z",
        },
        "comments": [],
        "review_comments": [],
        "files": [],
    }

    # 既存のPR番号を1つ選んで更新用のサンプルを作成
    update_pr_number = pr_numbers[0] if pr_numbers else None
    sample_update_pr = None
    if update_pr_number:
        sample_update_pr = {
            "basic_info": {
                "number": update_pr_number,
                "title": "更新されたPR",
                "state": "closed",
                "created_at": existing_pr_map[update_pr_number].get("basic_info", {}).get("created_at"),
                "updated_at": "2025-05-21T00:00:00Z",
            },
            "comments": [],
            "review_comments": [],
            "files": [],
        }

    # 新しいPRデータのリスト
    new_prs_data = []
    if sample_update_pr:
        new_prs_data.append(sample_update_pr)
        print(f"更新用サンプルPR #{update_pr_number} を追加")
    new_prs_data.append(sample_new_pr)
    print("新規サンプルPR #9999 を追加")

    # マージ処理のシミュレーション
    new_count = 0
    update_count = 0

    for pr in new_prs_data:
        pr_number = pr.get("basic_info", {}).get("number")
        if not pr_number:
            continue

        if pr_number in existing_pr_map:
            print(f"PR #{pr_number} を更新")
            update_count += 1
        else:
            print(f"PR #{pr_number} を新規追加")
            new_count += 1

    print(f"\nシミュレーション結果: 新規追加={new_count}件, 更新={update_count}件")
    print(f"実際のマージ後の合計PR数: {len(existing_pr_map) + new_count}")


if __name__ == "__main__":
    print("merge_with_existing_data関数の観察を開始します...")
    observe_merge_data()
    print("\n観察が完了しました。")
