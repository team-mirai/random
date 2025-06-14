#!/usr/bin/env python3
"""
PR Reporter CLI

GitHub Pull Requestデータからレポートを生成するためのコマンドラインインターフェース。
"""

import argparse
import os
import sys
from typing import Optional

from ..reporter import (
    generate_markdown,
    generate_summary_markdown,
    generate_issues_and_diffs_markdown,
    generate_file_based_markdown,
    convert_json_to_csv,
)
from ..utils import load_json_file


def main() -> int:
    """
    PR Reporterのメイン関数

    Returns:
        終了コード（成功: 0, 失敗: 1）
    """
    parser = argparse.ArgumentParser(description="GitHub Pull Requestデータからレポートを生成するツール")
    
    parser.add_argument("--input", required=True, help="入力JSONファイルパス")
    
    parser.add_argument(
        "--format",
        default="markdown",
        choices=["markdown", "summary", "issues", "files", "csv", "id_comment", "stats"],
        help="レポート形式",
    )
    
    parser.add_argument("--output", help="出力ファイルパスまたはディレクトリ")
    
    args = parser.parse_args()
    
    try:
        prs_data = load_json_file(args.input)
        if not prs_data:
            print(f"エラー: 入力ファイル {args.input} が空か、読み込めませんでした", file=sys.stderr)
            return 1
            
        print(f"{len(prs_data)} 件のPull Requestデータを読み込みました")
        
        output_file = args.output
        if not output_file:
            input_dir = os.path.dirname(args.input)
            input_name = os.path.splitext(os.path.basename(args.input))[0]
            
            if args.format == "markdown":
                output_file = os.path.join(input_dir, f"{input_name}_report.md")
            elif args.format == "summary":
                output_file = os.path.join(input_dir, f"{input_name}_summary.md")
            elif args.format == "issues":
                output_file = os.path.join(input_dir, f"{input_name}_issues_diffs.md")
            elif args.format == "files":
                output_file = os.path.join(input_dir, f"{input_name}_files")
            elif args.format in ["csv", "id_comment", "stats"]:
                output_file = os.path.join(input_dir, f"{input_name}.csv")
        
        if args.format == "markdown":
            generate_markdown(prs_data, output_file)
        elif args.format == "summary":
            generate_summary_markdown(prs_data, output_file)
        elif args.format == "issues":
            generate_issues_and_diffs_markdown(prs_data, output_file)
        elif args.format == "files":
            generate_file_based_markdown(prs_data, output_file)
        elif args.format == "csv":
            convert_json_to_csv(prs_data, output_file)
        elif args.format == "id_comment":
            convert_json_to_csv(
                prs_data,
                output_file,
                columns=["id", "comment"],
                extract_fields={
                    "id": "basic_info.number",
                    "comment": "basic_info.body",
                },
            )
        elif args.format == "stats":
            convert_json_to_csv(
                prs_data,
                output_file,
                columns=[
                    "id", "title", "state", "user", "created_at", "updated_at",
                    "commits", "comments", "review_comments", "files",
                    "additions", "deletions", "changes", "labels",
                ],
                extract_fields={
                    "id": "basic_info.number",
                    "title": "basic_info.title",
                    "state": "basic_info.state",
                    "user": "basic_info.user.login",
                    "created_at": "basic_info.created_at",
                    "updated_at": "basic_info.updated_at",
                },
            )
        
        print(f"レポートを {output_file} に生成しました")
        return 0
    except Exception as e:
        print(f"エラーが発生しました: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
