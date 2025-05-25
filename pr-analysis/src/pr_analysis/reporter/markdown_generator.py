"""
マークダウンレポート生成モジュール

Pull Requestデータからマークダウン形式のレポートを生成するための機能を提供します。
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union


def generate_markdown(data: List[Dict[str, Any]], output_file: str) -> None:
    """
    Pull Requestデータからマークダウンレポートを生成する

    Args:
        data: PRデータのリスト
        output_file: 出力ファイルパス
    """
    if not data:
        print("データが空です。マークダウンレポートを生成できません。")
        return

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Pull Request分析レポート\n\n")

        f.write("## 概要\n\n")
        f.write(f"- 分析対象PR数: {len(data)}\n")
        f.write(f"- 生成日時: {os.path.basename(output_file).split('_')[0]}\n\n")

        f.write("## Pull Requestリスト\n\n")

        for pr in data:
            basic_info = pr.get("basic_info", {})
            pr_number = basic_info.get("number")
            pr_title = basic_info.get("title")
            pr_state = basic_info.get("state")
            pr_user = basic_info.get("user", {}).get("login")
            pr_created_at = basic_info.get("created_at")
            pr_updated_at = basic_info.get("updated_at")
            pr_html_url = basic_info.get("html_url")

            if not pr_number or not pr_title:
                continue

            f.write(f"### PR #{pr_number}: {pr_title}\n\n")
            f.write(f"- 状態: {pr_state}\n")
            f.write(f"- 作成者: {pr_user}\n")
            f.write(f"- 作成日時: {pr_created_at}\n")
            f.write(f"- 更新日時: {pr_updated_at}\n")
            f.write(f"- URL: {pr_html_url}\n\n")

            labels = pr.get("labels", [])
            if labels:
                f.write("#### ラベル\n\n")
                for label in labels:
                    label_name = label.get("name")
                    if label_name:
                        f.write(f"- {label_name}\n")
                f.write("\n")

            commits = pr.get("commits", [])
            if commits:
                f.write("#### コミット\n\n")
                f.write(f"コミット数: {len(commits)}\n\n")
                for commit in commits[:5]:  # 最初の5件のみ表示
                    commit_info = commit.get("commit", {})
                    commit_message = commit_info.get("message", "").split("\n")[0]  # 1行目のみ
                    commit_author = commit_info.get("author", {}).get("name")
                    commit_date = commit_info.get("author", {}).get("date")
                    f.write(f"- {commit_message} (by {commit_author} on {commit_date})\n")
                if len(commits) > 5:
                    f.write(f"- ... 他 {len(commits) - 5} 件のコミット\n")
                f.write("\n")

            files = pr.get("files", [])
            if files:
                f.write("#### 変更ファイル\n\n")
                f.write(f"変更ファイル数: {len(files)}\n\n")
                for file in files[:10]:  # 最初の10件のみ表示
                    filename = file.get("filename")
                    status = file.get("status")
                    additions = file.get("additions", 0)
                    deletions = file.get("deletions", 0)
                    f.write(f"- {filename} ({status}, +{additions}, -{deletions})\n")
                if len(files) > 10:
                    f.write(f"- ... 他 {len(files) - 10} 件のファイル\n")
                f.write("\n")

            comments = pr.get("comments", [])
            review_comments = pr.get("review_comments", [])
            if comments or review_comments:
                f.write("#### コメント\n\n")
                f.write(f"コメント数: {len(comments)}, レビューコメント数: {len(review_comments)}\n\n")
                f.write("\n")

            f.write("---\n\n")

    print(f"マークダウンレポートを {output_file} に生成しました")


def generate_summary_markdown(data: List[Dict[str, Any]], output_file: str) -> None:
    """
    Pull Requestデータから要約マークダウンレポートを生成する

    Args:
        data: PRデータのリスト
        output_file: 出力ファイルパス
    """
    if not data:
        print("データが空です。要約マークダウンレポートを生成できません。")
        return

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    state_counts = {"open": 0, "closed": 0}
    
    user_pr_counts = {}
    
    label_counts = {}
    
    for pr in data:
        basic_info = pr.get("basic_info", {})
        
        state = basic_info.get("state")
        if state:
            state_counts[state] = state_counts.get(state, 0) + 1
        
        user = basic_info.get("user", {}).get("login")
        if user:
            user_pr_counts[user] = user_pr_counts.get(user, 0) + 1
        
        labels = pr.get("labels", [])
        for label in labels:
            label_name = label.get("name")
            if label_name:
                label_counts[label_name] = label_counts.get(label_name, 0) + 1

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Pull Request概要\n\n")

        f.write("## 統計情報\n\n")
        f.write(f"- 分析対象PR数: {len(data)}\n")
        f.write(f"- オープンなPR: {state_counts.get('open', 0)}\n")
        f.write(f"- クローズされたPR: {state_counts.get('closed', 0)}\n\n")

        f.write("## ユーザー別PR数\n\n")
        for user, count in sorted(user_pr_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- {user}: {count}\n")
        f.write("\n")

        if label_counts:
            f.write("## ラベル別PR数\n\n")
            for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- {label}: {count}\n")
            f.write("\n")

        f.write("## オープンなPull Requestの統計\n\n")
        open_prs = [pr for pr in data if pr.get("basic_info", {}).get("state") == "open"]
        if open_prs:
            open_prs.sort(key=lambda x: x.get("basic_info", {}).get("created_at", ""))
            
            f.write("### 最も古いオープンなPR\n\n")
            oldest_pr = open_prs[0]
            oldest_pr_info = oldest_pr.get("basic_info", {})
            f.write(f"- PR #{oldest_pr_info.get('number')}: {oldest_pr_info.get('title')}\n")
            f.write(f"- 作成者: {oldest_pr_info.get('user', {}).get('login')}\n")
            f.write(f"- 作成日時: {oldest_pr_info.get('created_at')}\n")
            f.write(f"- URL: {oldest_pr_info.get('html_url')}\n\n")
            
            open_prs.sort(key=lambda x: x.get("basic_info", {}).get("updated_at", ""), reverse=True)
            
            f.write("### 最近更新されたオープンなPR\n\n")
            recent_pr = open_prs[0]
            recent_pr_info = recent_pr.get("basic_info", {})
            f.write(f"- PR #{recent_pr_info.get('number')}: {recent_pr_info.get('title')}\n")
            f.write(f"- 作成者: {recent_pr_info.get('user', {}).get('login')}\n")
            f.write(f"- 更新日時: {recent_pr_info.get('updated_at')}\n")
            f.write(f"- URL: {recent_pr_info.get('html_url')}\n\n")
        else:
            f.write("オープンなPRはありません。\n\n")

    print(f"要約マークダウンレポートを {output_file} に生成しました")


def generate_issues_and_diffs_markdown(data: List[Dict[str, Any]], output_file: str) -> None:
    """
    Pull Requestデータからissues内容と変更差分のマークダウンレポートを生成する

    Args:
        data: PRデータのリスト
        output_file: 出力ファイルパス
    """
    if not data:
        print("データが空です。issues内容と変更差分のマークダウンレポートを生成できません。")
        return

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Pull Request内容と変更差分\n\n")

        for pr in data:
            basic_info = pr.get("basic_info", {})
            pr_number = basic_info.get("number")
            pr_title = basic_info.get("title")
            pr_body = basic_info.get("body", "")
            pr_html_url = basic_info.get("html_url")

            if not pr_number or not pr_title:
                continue

            f.write(f"## PR #{pr_number}: {pr_title}\n\n")
            f.write(f"URL: {pr_html_url}\n\n")

            if pr_body:
                f.write("### PR内容\n\n")
                f.write(f"{pr_body}\n\n")
            else:
                f.write("PR本文はありません。\n\n")

            f.write("### 変更内容\n\n")
            
            files = pr.get("files", [])
            if files:
                for file in files:
                    filename = file.get("filename")
                    status = file.get("status")
                    additions = file.get("additions", 0)
                    deletions = file.get("deletions", 0)
                    patch = file.get("patch")
                    
                    f.write(f"#### {filename}\n\n")
                    f.write(f"- 状態: {status}\n")
                    f.write(f"- 追加行数: {additions}\n")
                    f.write(f"- 削除行数: {deletions}\n")
                    
                    if patch:
                        f.write("\n```diff\n")
                        f.write(patch)
                        f.write("\n```\n\n")
                    else:
                        f.write("\n変更差分は利用できません。\n\n")
            else:
                f.write("変更ファイルはありません。\n\n")

            f.write("---\n\n")

    print(f"issues内容と変更差分のマークダウンレポートを {output_file} に生成しました")


def generate_file_based_markdown(data: List[Dict[str, Any]], output_dir: str) -> None:
    """
    Pull Requestデータからファイルごとのマークダウンレポートを生成する

    Args:
        data: PRデータのリスト
        output_dir: 出力ディレクトリ
    """
    if not data:
        print("データが空です。ファイルごとのマークダウンレポートを生成できません。")
        return

    os.makedirs(output_dir, exist_ok=True)

    file_prs = {}
    
    for pr in data:
        basic_info = pr.get("basic_info", {})
        pr_number = basic_info.get("number")
        pr_title = basic_info.get("title")
        pr_html_url = basic_info.get("html_url")
        
        if not pr_number or not pr_title:
            continue
            
        files = pr.get("files", [])
        for file in files:
            filename = file.get("filename")
            if not filename:
                continue
                
            if filename not in file_prs:
                file_prs[filename] = []
                
            file_prs[filename].append({
                "pr_number": pr_number,
                "pr_title": pr_title,
                "pr_url": pr_html_url,
                "status": file.get("status"),
                "additions": file.get("additions", 0),
                "deletions": file.get("deletions", 0),
                "patch": file.get("patch"),
            })

    for filename, prs in file_prs.items():
        file_path = Path(output_dir) / f"{filename.replace('/', '_')}.md"
        os.makedirs(file_path.parent, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# ファイル: {filename}\n\n")
            f.write(f"このファイルに影響を与えたPR数: {len(prs)}\n\n")
            
            for pr_info in prs:
                f.write(f"## PR #{pr_info['pr_number']}: {pr_info['pr_title']}\n\n")
                f.write(f"- URL: {pr_info['pr_url']}\n")
                f.write(f"- 状態: {pr_info['status']}\n")
                f.write(f"- 追加行数: {pr_info['additions']}\n")
                f.write(f"- 削除行数: {pr_info['deletions']}\n\n")
                
                patch = pr_info.get("patch")
                if patch:
                    f.write("### 変更差分\n\n")
                    f.write("```diff\n")
                    f.write(patch)
                    f.write("\n```\n\n")
                
                f.write("---\n\n")

    print(f"ファイルごとのマークダウンレポートを {output_dir} に生成しました")
