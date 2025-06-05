"""
CSVレポート生成モジュール

Pull RequestデータからCSV形式のレポートを生成するための機能を提供します。
"""

import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union


def convert_json_to_csv(
    data: List[Dict[str, Any]], 
    output_file: Optional[str] = None, 
    columns: Optional[List[str]] = None,
    extract_fields: Optional[Dict[str, str]] = None
) -> str:
    """
    Pull Requestデータからカスタム列を持つCSVファイルを生成する

    Args:
        data: PRデータのリスト
        output_file: 出力ファイルパス（指定がない場合は入力ファイルと同じディレクトリに生成）
        columns: CSVに含める列名のリスト
        extract_fields: データから抽出するフィールドのマッピング（列名: JSONパス）

    Returns:
        生成されたCSVファイルのパス
    """
    if not data:
        print("データが空です。CSVレポートを生成できません。")
        return ""

    if columns is None:
        columns = ["id", "title", "state", "user", "created_at", "updated_at", "comment"]

    if extract_fields is None:
        extract_fields = {
            "id": "basic_info.number",
            "title": "basic_info.title",
            "state": "basic_info.state",
            "user": "basic_info.user.login",
            "created_at": "basic_info.created_at",
            "updated_at": "basic_info.updated_at",
            "comment": "basic_info.body",
        }

    if output_file is None:
        output_file = "prs_data.csv"

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(columns)

        count = 0
        for pr in data:
            row = []
            for column in columns:
                field_path = extract_fields.get(column, "")
                if not field_path:
                    row.append("")
                    continue

                value = pr
                for key in field_path.split("."):
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = ""
                        break

                row.append(value)

            writer.writerow(row)
            count += 1

    print(f"{count}行のデータをCSVファイル {output_file} に書き込みました")
    return output_file


def convert_pr_to_id_comment_csv(data: List[Dict[str, Any]], output_file: Optional[str] = None) -> str:
    """
    Pull RequestデータからID-コメントのCSVファイルを生成する（json_to_csv.pyの代替）

    Args:
        data: PRデータのリスト
        output_file: 出力ファイルパス（指定がない場合は入力ファイルと同じディレクトリに生成）

    Returns:
        生成されたCSVファイルのパス
    """
    if output_file is None:
        output_file = "prs_id_comment.csv"

    columns = ["id", "comment"]
    extract_fields = {
        "id": "basic_info.number",
        "comment": "basic_info.body",
    }

    return convert_json_to_csv(data, output_file, columns, extract_fields)


def convert_pr_to_stats_csv(data: List[Dict[str, Any]], output_file: Optional[str] = None) -> str:
    """
    Pull RequestデータからPR統計情報のCSVファイルを生成する

    Args:
        data: PRデータのリスト
        output_file: 出力ファイルパス（指定がない場合は入力ファイルと同じディレクトリに生成）

    Returns:
        生成されたCSVファイルのパス
    """
    if output_file is None:
        output_file = "prs_stats.csv"

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "id", "title", "state", "user", "created_at", "updated_at",
            "commits", "comments", "review_comments", "files",
            "additions", "deletions", "changes", "labels"
        ])

        count = 0
        for pr in data:
            basic_info = pr.get("basic_info", {})
            
            pr_id = basic_info.get("number", "")
            title = basic_info.get("title", "")
            state = basic_info.get("state", "")
            user = basic_info.get("user", {}).get("login", "")
            created_at = basic_info.get("created_at", "")
            updated_at = basic_info.get("updated_at", "")
            
            commits = len(pr.get("commits", []))
            comments = len(pr.get("comments", []))
            review_comments = len(pr.get("review_comments", []))
            
            files = pr.get("files", [])
            file_count = len(files)
            
            additions = sum(file.get("additions", 0) for file in files)
            deletions = sum(file.get("deletions", 0) for file in files)
            changes = additions + deletions
            
            labels = ", ".join([label.get("name", "") for label in pr.get("labels", [])])
            
            writer.writerow([
                pr_id, title, state, user, created_at, updated_at,
                commits, comments, review_comments, file_count,
                additions, deletions, changes, labels
            ])
            count += 1

    print(f"{count}行のデータをCSVファイル {output_file} に書き込みました")
    return output_file
