#!/usr/bin/env python3
"""
PR Fetcher CLI

GitHub Pull Requestデータを取得するためのコマンドラインインターフェース。
"""

import argparse
import datetime
import os
import sys
from typing import Optional

from ..fetcher import fetch_prs


def main() -> int:
    """
    PR Fetcherのメイン関数

    Returns:
        終了コード（成功: 0, 失敗: 1）
    """
    parser = argparse.ArgumentParser(description="GitHub Pull Requestデータを取得するツール")
    
    parser.add_argument("--owner", required=True, help="リポジトリのオーナー名")
    parser.add_argument("--repo", required=True, help="リポジトリ名")
    
    parser.add_argument("--limit", type=int, help="取得するPRの最大数")
    parser.add_argument("--state", default="all", choices=["open", "closed", "all"], help="PRの状態")
    parser.add_argument("--sort-by", default="updated", choices=["created", "updated", "popularity", "long-running"], help="ソート基準")
    parser.add_argument("--direction", default="desc", choices=["asc", "desc"], help="ソート方向")
    
    parser.add_argument("--no-comments", action="store_true", help="コメントを含めない")
    parser.add_argument("--no-review-comments", action="store_true", help="レビューコメントを含めない")
    parser.add_argument("--no-commits", action="store_true", help="コミット情報を含めない")
    parser.add_argument("--no-files", action="store_true", help="変更ファイル情報を含めない")
    parser.add_argument("--no-labels", action="store_true", help="ラベル情報を含めない")
    
    parser.add_argument("--max-workers", type=int, default=4, help="並列処理の最大ワーカー数")
    
    parser.add_argument("--output-dir", help="出力ディレクトリ")
    parser.add_argument("--incremental", action="store_true", help="増分更新を行う")
    
    parser.add_argument("--fetch-mode", default="api", choices=["api", "sequential", "priority"], help="取得モード")
    parser.add_argument("--start-id", type=int, default=1, help="取得開始ID（sequential モードの場合）")
    parser.add_argument("--max-id", type=int, help="取得終了ID（sequential モードの場合）")
    
    args = parser.parse_args()
    
    try:
        prs_data = fetch_prs(
            repo_owner=args.owner,
            repo_name=args.repo,
            limit=args.limit,
            state=args.state,
            sort_by=args.sort_by,
            direction=args.direction,
            include_comments=not args.no_comments,
            include_review_comments=not args.no_review_comments,
            include_commits=not args.no_commits,
            include_files=not args.no_files,
            include_labels=not args.no_labels,
            max_workers=args.max_workers,
            output_dir=args.output_dir,
            incremental=args.incremental,
            fetch_mode=args.fetch_mode,
            start_id=args.start_id,
            max_id=args.max_id,
        )
        
        print(f"{len(prs_data)} 件のPull Requestデータを取得しました")
        return 0
    except Exception as e:
        print(f"エラーが発生しました: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
