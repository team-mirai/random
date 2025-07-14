"""
PR Analyzer モジュール

GitHub Pull Requestデータを分析するための機能を提供します。
"""

import datetime
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

from ..api.github import GitHubAPIClient
from .content_classifier import ContentClassifier, is_readme_pr


class PRAnalyzer:
    """Pull Requestデータを分析するためのクラス"""

    def __init__(self, repo_owner: str, repo_name: str):
        """
        PRAnalyzerを初期化する

        Args:
            repo_owner: リポジトリのオーナー名
            repo_name: リポジトリ名
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_client = GitHubAPIClient(repo_owner, repo_name)
        self.content_classifier = ContentClassifier()

    def analyze_pr(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        1つのPRを分析する

        Args:
            pr_data: 分析するPR情報

        Returns:
            分析結果を含む辞書
        """
        analysis_result = {
            "pr_id": pr_data.get("basic_info", {}).get("number"),
            "is_readme_pr": is_readme_pr(pr_data),
            "file_stats": self._analyze_files(pr_data.get("files", [])),
            "commit_stats": self._analyze_commits(pr_data.get("commits", [])),
            "comment_stats": self._analyze_comments(
                pr_data.get("comments", []), pr_data.get("review_comments", [])
            ),
            "labels": [label.get("name") for label in pr_data.get("labels", [])],
            "created_at": pr_data.get("basic_info", {}).get("created_at"),
            "updated_at": pr_data.get("basic_info", {}).get("updated_at"),
            "state": pr_data.get("basic_info", {}).get("state"),
            "user": pr_data.get("basic_info", {}).get("user", {}).get("login"),
        }

        basic_info = pr_data.get("basic_info", {})
        title = basic_info.get("title", "")
        body = basic_info.get("body", "")
        content = f"{title}\n\n{body}"

        if content.strip():
            categories = ["バグ修正", "機能追加", "リファクタリング", "ドキュメント", "テスト", "設定変更"]
            try:
                classification = self.content_classifier.classify_content(content, categories)
                analysis_result["classification"] = classification
            except Exception as e:
                print(f"PR #{analysis_result['pr_id']} の内容分類中にエラーが発生しました: {e}")

        return analysis_result

    def _analyze_files(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        PRの変更ファイルを分析する

        Args:
            files: 変更ファイル情報のリスト

        Returns:
            ファイル分析結果
        """
        if not files:
            return {"total_files": 0}

        extensions = {}
        total_additions = 0
        total_deletions = 0
        total_changes = 0
        file_paths = []

        for file in files:
            filename = file.get("filename", "")
            file_paths.append(filename)

            ext = os.path.splitext(filename)[1].lower()
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1

            additions = file.get("additions", 0)
            deletions = file.get("deletions", 0)
            changes = file.get("changes", 0)

            total_additions += additions
            total_deletions += deletions
            total_changes += changes

        return {
            "total_files": len(files),
            "extensions": extensions,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "total_changes": total_changes,
            "file_paths": file_paths,
        }

    def _analyze_commits(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        PRのコミットを分析する

        Args:
            commits: コミット情報のリスト

        Returns:
            コミット分析結果
        """
        if not commits:
            return {"total_commits": 0}

        commit_messages = []
        authors = set()

        for commit in commits:
            message = commit.get("commit", {}).get("message", "")
            if message:
                commit_messages.append(message)

            author = commit.get("author", {})
            if author and "login" in author:
                authors.add(author["login"])

        return {
            "total_commits": len(commits),
            "commit_messages": commit_messages,
            "unique_authors": list(authors),
        }

    def _analyze_comments(
        self, comments: List[Dict[str, Any]], review_comments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        PRのコメントを分析する

        Args:
            comments: コメント情報のリスト
            review_comments: レビューコメント情報のリスト

        Returns:
            コメント分析結果
        """
        total_comments = len(comments) + len(review_comments)
        if total_comments == 0:
            return {"total_comments": 0}

        comment_authors = set()
        review_comment_authors = set()

        for comment in comments:
            author = comment.get("user", {}).get("login")
            if author:
                comment_authors.add(author)

        for comment in review_comments:
            author = comment.get("user", {}).get("login")
            if author:
                review_comment_authors.add(author)

        return {
            "total_comments": total_comments,
            "issue_comments": len(comments),
            "review_comments": len(review_comments),
            "comment_authors": list(comment_authors),
            "review_comment_authors": list(review_comment_authors),
            "all_comment_authors": list(comment_authors.union(review_comment_authors)),
        }

    def analyze_prs(self, prs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        複数のPRを分析する

        Args:
            prs_data: 分析するPR情報のリスト

        Returns:
            分析結果のリスト
        """
        analysis_results = []
        for pr_data in prs_data:
            try:
                result = self.analyze_pr(pr_data)
                analysis_results.append(result)
            except Exception as e:
                pr_id = pr_data.get("basic_info", {}).get("number", "不明")
                print(f"PR #{pr_id} の分析中にエラーが発生しました: {e}")

        return analysis_results

    def save_analysis_results(self, results: List[Dict[str, Any]], output_file: str) -> None:
        """
        分析結果をJSON形式で保存する

        Args:
            results: 保存する分析結果
            output_file: 保存先ファイル名
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"分析結果を {output_file} に保存しました")

    def generate_summary_stats(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析結果から要約統計を生成する

        Args:
            analysis_results: 分析結果のリスト

        Returns:
            要約統計情報
        """
        if not analysis_results:
            return {"total_prs": 0}

        state_counts = {"open": 0, "closed": 0, "merged": 0}
        
        user_pr_counts = {}
        
        extension_counts = {}
        
        total_additions = 0
        total_deletions = 0
        total_changes = 0
        
        total_files = 0
        
        total_commits = 0
        
        total_comments = 0
        
        label_counts = {}
        
        date_pr_counts = {}
        
        for result in analysis_results:
            state = result.get("state", "")
            if state == "closed" and result.get("basic_info", {}).get("merged", False):
                state = "merged"
            state_counts[state] = state_counts.get(state, 0) + 1
            
            user = result.get("user", "")
            if user:
                user_pr_counts[user] = user_pr_counts.get(user, 0) + 1
            
            file_stats = result.get("file_stats", {})
            extensions = file_stats.get("extensions", {})
            for ext, count in extensions.items():
                extension_counts[ext] = extension_counts.get(ext, 0) + count
            
            total_additions += file_stats.get("total_additions", 0)
            total_deletions += file_stats.get("total_deletions", 0)
            total_changes += file_stats.get("total_changes", 0)
            total_files += file_stats.get("total_files", 0)
            
            commit_stats = result.get("commit_stats", {})
            total_commits += commit_stats.get("total_commits", 0)
            
            comment_stats = result.get("comment_stats", {})
            total_comments += comment_stats.get("total_comments", 0)
            
            labels = result.get("labels", [])
            for label in labels:
                label_counts[label] = label_counts.get(label, 0) + 1
            
            created_at = result.get("created_at", "")
            if created_at:
                date = created_at.split("T")[0]  # YYYY-MM-DD形式
                date_pr_counts[date] = date_pr_counts.get(date, 0) + 1
        
        return {
            "total_prs": len(analysis_results),
            "state_counts": state_counts,
            "user_pr_counts": user_pr_counts,
            "extension_counts": extension_counts,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "total_changes": total_changes,
            "total_files": total_files,
            "total_commits": total_commits,
            "total_comments": total_comments,
            "label_counts": label_counts,
            "date_pr_counts": date_pr_counts,
        }


def analyze_prs(
    prs_data: List[Dict[str, Any]],
    repo_owner: str,
    repo_name: str,
    output_file: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Pull Requestデータを分析する便利関数

    Args:
        prs_data: 分析するPR情報のリスト
        repo_owner: リポジトリのオーナー名
        repo_name: リポジトリ名
        output_file: 分析結果の保存先ファイル名

    Returns:
        分析結果のリスト
    """
    analyzer = PRAnalyzer(repo_owner, repo_name)
    results = analyzer.analyze_prs(prs_data)
    
    if output_file:
        analyzer.save_analysis_results(results, output_file)
    
    return results
