#!/usr/bin/env python3
"""
PR分析データ統合スクリプト

複数のpr_analysis_resultsディレクトリにあるprs_data.jsonファイルを統合し、
一つの統合されたJSONファイルを作成します。また、今後の更新時には既存の統合ファイルを
更新することができます。
"""

import argparse
import glob
import json
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_json_file(file_path):
    """JSONファイルを読み込む"""
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return []


def save_json_file(data, file_path):
    """JSONファイルを保存する"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved merged data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to {file_path}: {e}")
        return False


def merge_pr_data(input_dirs=None, output_file=None, update_existing=True):
    """
    複数のディレクトリからPRデータを統合する

    Args:
        input_dirs: 入力ディレクトリのリスト（指定がない場合は全てのpr_analysis_resultsディレクトリを使用）
        output_file: 出力ファイルパス
        update_existing: 既存の統合ファイルを更新するかどうか

    Returns:
        統合されたデータの数
    """
    if output_file is None:
        output_file = os.path.join("pr_analysis_results", "merged", "merged_prs_data.json")

    existing_data = []
    existing_pr_ids = set()
    if update_existing and os.path.exists(output_file):
        existing_data = load_json_file(output_file)
        existing_pr_ids = {pr.get("basic_info", {}).get("id") for pr in existing_data if "basic_info" in pr}
        logger.info(f"Loaded {len(existing_data)} existing PRs from {output_file}")

    if input_dirs is None:
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pr_analysis_results")
        input_dirs = [d for d in glob.glob(os.path.join(base_dir, "*")) if os.path.isdir(d)]

    all_prs = []
    for input_dir in input_dirs:
        data_file = os.path.join(input_dir, "prs_data.json")
        if os.path.exists(data_file):
            prs_data = load_json_file(data_file)
            logger.info(f"Loaded {len(prs_data)} PRs from {data_file}")
            all_prs.extend(prs_data)

    merged_data = existing_data.copy() if update_existing else []
    new_count = 0

    for pr in all_prs:
        pr_id = pr.get("basic_info", {}).get("id")
        if pr_id and pr_id not in existing_pr_ids:
            merged_data.append(pr)
            existing_pr_ids.add(pr_id)
            new_count += 1

    if save_json_file(merged_data, output_file):
        logger.info(f"Merged data saved successfully. Added {new_count} new PRs, total: {len(merged_data)}")

    return len(merged_data)


def main():
    parser = argparse.ArgumentParser(description="Merge PR data from multiple directories")
    parser.add_argument(
        "--input-dirs",
        nargs="+",
        help="Input directories containing prs_data.json files (default: all pr_analysis_results directories)",
    )
    parser.add_argument(
        "--output-file",
        default=os.path.join("pr_analysis_results", "merged", "merged_prs_data.json"),
        help="Output file path for merged data",
    )
    parser.add_argument(
        "--no-update", action="store_true", help="Don't update existing merged file, create a new one instead"
    )
    parser.add_argument(
        "--specific-dirs",
        nargs="+",
        default=["20250521_021502", "20250521_034352", "20250521_034935", "20250521_094649"],
        help="Specific directory names to process (e.g. 20250521_034352)",
    )

    args = parser.parse_args()

    if args.specific_dirs:
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pr_analysis_results")
        input_dirs = [os.path.join(base_dir, d) for d in args.specific_dirs]
        logger.info(f"Processing specific directories: {args.specific_dirs}")
    else:
        input_dirs = args.input_dirs

    total_prs = merge_pr_data(input_dirs=input_dirs, output_file=args.output_file, update_existing=not args.no_update)

    logger.info(f"Completed merging PR data. Total PRs in merged file: {total_prs}")


if __name__ == "__main__":
    main()
