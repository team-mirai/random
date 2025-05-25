#!/usr/bin/env python3
"""
PR Analyzer CLI

GitHub Pull Requestデータを分析するためのコマンドラインインターフェース。
"""

import argparse
import os
import sys
from typing import Optional

from ..analyzer import analyze_prs
from ..utils import load_json_file


def main() -> int:
    """
    PR Analyzerのメイン関数

    Returns:
        終了コード（成功: 0, 失敗: 1）
    """
    parser = argparse.ArgumentParser(description="GitHub Pull Requestデータを分析するツール")
    
    parser.add_argument("--input", required=True, help="入力JSONファイルパス")
    
    parser.add_argument("--owner", required=True, help="リポジトリのオーナー名")
    parser.add_argument("--repo", required=True, help="リポジトリ名")
    
    parser.add_argument("--output", help="分析結果の出力ファイルパス")
    
    args = parser.parse_args()
    
    try:
        prs_data = load_json_file(args.input)
        if not prs_data:
            print(f"エラー: 入力ファイル {args.input} が空か、読み込めませんでした", file=sys.stderr)
            return 1
            
        print(f"{len(prs_data)} 件のPull Requestデータを読み込みました")
        
        results = analyze_prs(
            prs_data=prs_data,
            repo_owner=args.owner,
            repo_name=args.repo,
            output_file=args.output,
        )
        
        print(f"{len(results)} 件のPull Requestデータを分析しました")
        
        if args.output:
            print(f"分析結果を {args.output} に保存しました")
            
        return 0
    except Exception as e:
        print(f"エラーが発生しました: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
