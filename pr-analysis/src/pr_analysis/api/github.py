"""
GitHub API操作モジュール

GitHubのAPIを使用してPull Requestデータを取得するための機能を提供します。
"""

import datetime
import os
import time
from typing import Dict, List, Optional, Union, Any

import backoff
import requests
from tqdm import tqdm


class GitHubAPIClient:
    """GitHubのAPIを操作するためのクライアントクラス"""

    def __init__(self, repo_owner: str, repo_name: str, api_base_url: str = "https://api.github.com"):
        """
        GitHubAPIClientを初期化する

        Args:
            repo_owner: リポジトリのオーナー名
            repo_name: リポジトリ名
            api_base_url: GitHub APIのベースURL
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_base_url = api_base_url
        self.headers = self._get_headers()

    def _get_github_token(self) -> Optional[str]:
        """環境変数からGitHubトークンを取得する"""
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            try:
                import subprocess

                result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
                if result.returncode == 0:
                    token = result.stdout.strip()
            except Exception as e:
                print(f"gh CLIからトークンを取得できませんでした: {e}")

        return token

    def _get_headers(self) -> Dict[str, str]:
        """APIリクエスト用のヘッダーを取得する"""
        token = self._get_github_token()
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        return headers

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException, requests.exceptions.HTTPError),
        max_tries=5,  # 最大5回再試行
        max_time=30,  # 最大30秒
        giveup=lambda e: isinstance(e, requests.exceptions.HTTPError)
        and e.response.status_code in [401, 403, 404],  # 認証エラーやリソースが存在しない場合は再試行しない
    )
    def make_api_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        GitHubのAPIリクエストを実行し、再試行ロジックを適用する

        Args:
            url: リクエスト先のURL
            params: リクエストパラメータ

        Returns:
            APIレスポンスのJSONデータ
        """
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def check_rate_limit(self) -> tuple:
        """
        GitHub APIのレート制限状況を確認する

        Returns:
            (残りリクエスト数, リセット時間)のタプル
        """
        url = f"{self.api_base_url}/rate_limit"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        rate_limit_data = response.json()
        core_rate = rate_limit_data["resources"]["core"]

        remaining = core_rate["remaining"]
        reset_time = datetime.datetime.fromtimestamp(core_rate["reset"])
        now = datetime.datetime.now()

        print(f"API制限: 残り {remaining} リクエスト")
        print(f"制限リセット時間: {reset_time} (あと {(reset_time - now).total_seconds() / 60:.1f} 分)")

        return remaining, reset_time

    def get_pull_requests(
        self,
        limit: Optional[int] = None,
        sort_by: str = "updated",
        direction: str = "desc",
        last_updated_at: Optional[datetime.datetime] = None,
        state: str = "open",
    ) -> List[Dict[str, Any]]:
        """
        Pull Requestを取得する

        Args:
            limit: 取得するPRの最大数
            sort_by: ソート基準 ("created", "updated", "popularity", "long-running")
            direction: ソート方向 ("asc" or "desc")
            last_updated_at: 前回実行時の最新更新日時（この日時以降のPRのみ取得）
            state: PRの状態 ("open", "closed", "all")

        Returns:
            Pull Requestのリスト
        """
        all_prs = []
        page = 1
        per_page = 100

        while True:
            url = f"{self.api_base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls"
            params = {"state": state, "per_page": per_page, "page": page, "sort": sort_by, "direction": direction}

            try:
                prs = self.make_api_request(url, params=params)
                if not prs:
                    break

                if last_updated_at:
                    new_prs = []
                    for pr in prs:
                        pr_updated_at = datetime.datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
                        if pr_updated_at <= last_updated_at:
                            print(f"前回処理済みのPR #{pr['number']} に到達しました。処理を終了します。")
                            break
                        new_prs.append(pr)

                    if len(new_prs) < len(prs):
                        all_prs.extend(new_prs)
                        break

                    all_prs.extend(new_prs)
                else:
                    all_prs.extend(prs)

                page += 1

                if limit and len(all_prs) >= limit:
                    all_prs = all_prs[:limit]
                    break

                if page > 1:
                    time.sleep(0.5)  # APIレート制限を考慮して少し待機
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403 and "API rate limit exceeded" in e.response.text:
                    print("GitHubのAPIレート制限に達しました。処理を終了します。")
                    break
                print(f"PRリスト取得中にエラーが発生しました (ページ {page}): {e}")
                break
            except Exception as e:
                print(f"PRリスト取得中にエラーが発生しました (ページ {page}): {e}")
                break

        return all_prs

    def get_pr_by_number(self, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        PR番号を指定してPRを取得する

        Args:
            pr_number: PR番号

        Returns:
            PR情報の辞書、存在しない場合はNone
        """
        try:
            url = f"{self.api_base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}"
            return self.make_api_request(url)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"PR #{pr_number} は存在しません")
                return None
            raise

    def get_pr_comments(self, pr_number: int) -> List[Dict[str, Any]]:
        """
        PRのコメントを取得する

        Args:
            pr_number: PR番号

        Returns:
            コメントのリスト
        """
        url = f"{self.api_base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{pr_number}/comments"
        return self.make_api_request(url)

    def get_pr_review_comments(self, pr_number: int) -> List[Dict[str, Any]]:
        """
        PRのレビューコメントを取得する

        Args:
            pr_number: PR番号

        Returns:
            レビューコメントのリスト
        """
        url = f"{self.api_base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}/comments"
        return self.make_api_request(url)

    def get_pr_commits(self, pr_number: int) -> List[Dict[str, Any]]:
        """
        PRのコミット情報を取得する

        Args:
            pr_number: PR番号

        Returns:
            コミット情報のリスト
        """
        url = f"{self.api_base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}/commits"
        return self.make_api_request(url)

    def get_pr_files(self, pr_number: int) -> List[Dict[str, Any]]:
        """
        PRの変更ファイル情報を取得する

        Args:
            pr_number: PR番号

        Returns:
            変更ファイル情報のリスト
        """
        url = f"{self.api_base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}/files"
        return self.make_api_request(url)

    def get_pr_labels(self, pr_number: int) -> List[Dict[str, Any]]:
        """
        PRのラベル情報を取得する

        Args:
            pr_number: PR番号

        Returns:
            ラベル情報のリスト
        """
        url = f"{self.api_base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{pr_number}/labels"
        return self.make_api_request(url)

    def get_pr_details(
        self,
        pr_number: int,
        include_comments: bool = True,
        include_review_comments: bool = True,
        include_commits: bool = True,
        include_files: bool = True,
        include_labels: bool = True,
    ) -> Dict[str, Any]:
        """
        PRの詳細情報を取得する

        Args:
            pr_number: PR番号
            include_comments: コメントを含めるかどうか
            include_review_comments: レビューコメントを含めるかどうか
            include_commits: コミット情報を含めるかどうか
            include_files: 変更ファイル情報を含めるかどうか
            include_labels: ラベル情報を含めるかどうか

        Returns:
            PR詳細情報の辞書
        """
        pr_data = self.get_pr_by_number(pr_number)
        if not pr_data:
            return {}

        pr_details = {
            "basic_info": pr_data,
            "state": pr_data["state"],  # open または closed
            "updated_at": pr_data["updated_at"],  # 更新日時を保存
        }

        if include_labels:
            try:
                pr_details["labels"] = self.get_pr_labels(pr_number)
            except Exception as e:
                print(f"PR #{pr_number} のラベル取得中にエラーが発生しました: {str(e)[:200]}")
                pr_details["labels"] = []

        if include_comments:
            pr_details["comments"] = self.get_pr_comments(pr_number)

        if include_review_comments:
            pr_details["review_comments"] = self.get_pr_review_comments(pr_number)

        if include_commits:
            pr_details["commits"] = self.get_pr_commits(pr_number)

        if include_files:
            pr_details["files"] = self.get_pr_files(pr_number)

        return pr_details
