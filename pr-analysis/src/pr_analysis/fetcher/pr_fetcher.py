"""
PR Fetcher モジュール

GitHub Pull Requestデータを取得するための機能を提供します。
"""

import concurrent.futures
import datetime
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from tqdm import tqdm

from ..api.github import GitHubAPIClient


class PRFetcher:
    """Pull Requestデータを取得するためのクラス"""

    def __init__(self, repo_owner: str, repo_name: str, output_dir: str = "pr_analysis_results"):
        """
        PRFetcherを初期化する

        Args:
            repo_owner: リポジトリのオーナー名
            repo_name: リポジトリ名
            output_dir: 出力ディレクトリ
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.output_dir = output_dir
        self.github_client = GitHubAPIClient(repo_owner, repo_name)

    def process_pr(
        self,
        pr: Dict[str, Any],
        include_comments: bool = True,
        include_review_comments: bool = True,
        include_commits: bool = True,
        include_files: bool = True,
        include_labels: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        1つのPRを処理する（並列処理用）

        Args:
            pr: 処理するPR情報
            include_comments: コメントを含めるかどうか
            include_review_comments: レビューコメントを含めるかどうか
            include_commits: コミット情報を含めるかどうか
            include_files: 変更ファイル情報を含めるかどうか
            include_labels: ラベル情報を含めるかどうか

        Returns:
            処理されたPR詳細情報
        """
        try:
            pr_number = pr["number"]
            try:
                return self.github_client.get_pr_details(
                    pr_number,
                    include_comments=include_comments,
                    include_review_comments=include_review_comments,
                    include_commits=include_commits,
                    include_files=include_files,
                    include_labels=include_labels,
                )
            except Exception as e:
                print(f"PR #{pr_number} の処理中にエラーが発生しました: {str(e)[:200]}")
                return None
        except Exception as e:
            print(f"PRのbasic_info取得中にエラーが発生しました: {str(e)[:200]}")
            return None

    def save_to_json(self, data: List[Dict[str, Any]], filename: str) -> None:
        """
        データをJSON形式で保存する

        Args:
            data: 保存するデータ
            filename: 保存先ファイル名
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"JSONデータを {filename} に保存しました")

    def save_last_run_info(self, output_dir: str, last_updated_at: datetime.datetime) -> None:
        """
        最後の実行情報を保存する

        Args:
            output_dir: 出力ディレクトリ
            last_updated_at: 最終更新日時
        """
        last_run_info = {
            "last_updated_at": last_updated_at.isoformat(),
            "timestamp": datetime.datetime.now().isoformat()
        }

        last_run_file = Path(output_dir) / "last_run_info.json"
        with open(last_run_file, "w", encoding="utf-8") as f:
            json.dump(last_run_info, f, ensure_ascii=False, indent=2)
        print(f"最後の実行情報を {last_run_file} に保存しました")

    def load_last_run_info(self, base_output_dir: str) -> Optional[datetime.datetime]:
        """
        最後の実行情報を読み込む

        Args:
            base_output_dir: 基本出力ディレクトリ

        Returns:
            最終更新日時
        """
        last_run_file = Path(base_output_dir) / "last_run_info.json"

        if last_run_file.exists():
            try:
                with open(last_run_file, encoding="utf-8") as f:
                    last_run_info = json.load(f)

                last_updated_at = datetime.datetime.fromisoformat(last_run_info["last_updated_at"])
                print(f"前回の実行情報を読み込みました: 最終更新日時 = {last_updated_at}")
                return last_updated_at
            except Exception as e:
                print(f"前回の実行情報の読み込み中にエラーが発生しました: {e}")

        print("前回の実行情報が見つかりませんでした")
        return None

    def load_previous_prs_data(self, base_output_dir: str) -> List[Dict[str, Any]]:
        """
        前回のPRデータを読み込む

        Args:
            base_output_dir: 基本出力ディレクトリ

        Returns:
            前回のPRデータ
        """
        dirs = [d for d in Path(base_output_dir).glob("*") if d.is_dir() and d.name[0].isdigit()]
        if not dirs:
            print("前回のPRデータが見つかりませんでした")
            return []

        latest_dir = max(dirs, key=lambda d: d.stat().st_mtime)
        json_file = latest_dir / "prs_data.json"

        if json_file.exists():
            try:
                with open(json_file, encoding="utf-8") as f:
                    prs_data = json.load(f)
                print(f"前回のPRデータを読み込みました: {len(prs_data)}件 ({json_file})")
                return prs_data
            except Exception as e:
                print(f"前回のPRデータの読み込み中にエラーが発生しました: {e}")

        print("前回のPRデータが見つかりませんでした")
        return []

    def load_pr_status_data(self, base_output_dir: str) -> Dict[str, Any]:
        """
        PRの取得状況データを読み込む

        Args:
            base_output_dir: 基本出力ディレクトリ

        Returns:
            PRの取得状況データ
        """
        status_file = Path(base_output_dir) / "pr_status.json"

        if status_file.exists():
            try:
                with open(status_file, encoding="utf-8") as f:
                    status_data = json.load(f)
                print(f"PRの取得状況データを読み込みました: {len(status_data)}件のPR")
                return status_data
            except Exception as e:
                print(f"PRの取得状況データの読み込み中にエラーが発生しました: {e}")

        return {}

    def save_pr_status_data(self, base_output_dir: str, status_data: Dict[str, Any]) -> None:
        """
        PRの取得状況データを保存する

        Args:
            base_output_dir: 基本出力ディレクトリ
            status_data: PRの取得状況データ
        """
        status_file = Path(base_output_dir) / "pr_status.json"
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        print(f"PRの取得状況データを {status_file} に保存しました")

    def fetch_prs(
        self,
        limit: Optional[int] = None,
        state: str = "all",
        sort_by: str = "updated",
        direction: str = "desc",
        include_comments: bool = True,
        include_review_comments: bool = True,
        include_commits: bool = True,
        include_files: bool = True,
        include_labels: bool = True,
        max_workers: int = 4,
        output_dir: Optional[str] = None,
        incremental: bool = False,
        fetch_mode: str = "api",
        start_id: int = 1,
        max_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Pull Requestデータを取得する

        Args:
            limit: 取得するPRの最大数
            state: PRの状態 ("open", "closed", "all")
            sort_by: ソート基準 ("created", "updated", "popularity", "long-running")
            direction: ソート方向 ("asc" or "desc")
            include_comments: コメントを含めるかどうか
            include_review_comments: レビューコメントを含めるかどうか
            include_commits: コミット情報を含めるかどうか
            include_files: 変更ファイル情報を含めるかどうか
            include_labels: ラベル情報を含めるかどうか
            max_workers: 並列処理の最大ワーカー数
            output_dir: 出力ディレクトリ
            incremental: 増分更新を行うかどうか
            fetch_mode: 取得モード ("api", "sequential", "priority")
            start_id: 取得開始ID（sequential モードの場合）
            max_id: 取得終了ID（sequential モードの場合）

        Returns:
            取得したPRデータのリスト
        """
        if output_dir is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(self.output_dir, timestamp)

        os.makedirs(output_dir, exist_ok=True)
        print(f"出力ディレクトリ: {output_dir}")

        remaining, reset_time = self.github_client.check_rate_limit()
        if remaining < 10:
            wait_time = (reset_time - datetime.datetime.now()).total_seconds()
            if wait_time > 0:
                print(f"APIレート制限に近づいています。{wait_time:.1f}秒待機します...")
                time.sleep(wait_time + 5)  # 少し余裕を持たせる

        last_updated_at = None
        if incremental:
            last_updated_at = self.load_last_run_info(self.output_dir)

        status_data = {}
        if fetch_mode == "priority":
            status_data = self.load_pr_status_data(self.output_dir)

        print(f"Pull Requestの基本情報を取得しています...")
        basic_prs = []

        if fetch_mode == "api":
            basic_prs = self.github_client.get_pull_requests(
                limit=limit, sort_by=sort_by, direction=direction, last_updated_at=last_updated_at, state=state
            )
        elif fetch_mode == "sequential":
            current_id = start_id
            count = 0

            print(f"PR番号 #{start_id} から順にPRを取得します...")

            while True:
                try:
                    pr = self.github_client.get_pr_by_number(current_id)
                    if pr:
                        basic_prs.append(pr)
                        print(f"PR #{current_id} を取得しました")
                        count += 1
                    else:
                        print(f"PR #{current_id} は存在しないためスキップします")
                        if current_id > 100:  # 一定数以上のPRが存在しない場合は終了
                            print(f"PR #{current_id} が存在しないため、これ以上のPRは存在しないと判断して処理を終了します。")
                            break

                    current_id += 1

                    if max_id and current_id > max_id:
                        print(f"最大ID #{max_id} に到達しました。処理を終了します。")
                        break

                    if limit and count >= limit:
                        print(f"最大取得数 {limit} に到達しました。処理を終了します。")
                        break

                    time.sleep(0.5)

                except Exception as e:
                    print(f"PR #{current_id} の取得中にエラーが発生しました: {e}")
                    current_id += 1  # エラーが発生したら次のIDに進む
        elif fetch_mode == "priority":
            none_ids = [int(pr_id) for pr_id, fetch_time in status_data.items() if fetch_time is None]
            none_ids.sort()  # ID順にソート

            print(f"{len(none_ids)}件の未取得PRを優先的に取得します...")

            count = 0
            for pr_id in none_ids:
                try:
                    pr = self.github_client.get_pr_by_number(pr_id)
                    if pr:
                        basic_prs.append(pr)
                        print(f"PR #{pr_id} を取得しました")
                        count += 1
                    else:
                        print(f"PR #{pr_id} は存在しないためスキップします")

                    if limit and count >= limit:
                        print(f"最大取得数 {limit} に到達しました。処理を終了します。")
                        break

                    time.sleep(0.5)

                except Exception as e:
                    print(f"PR #{pr_id} の取得中にエラーが発生しました: {e}")

            if limit and count < limit:
                remaining_limit = limit - count
                print(f"未取得PRの取得が完了しました。残り {remaining_limit} 件を更新日時順で取得します...")

                additional_prs = self.github_client.get_pull_requests(
                    limit=remaining_limit, sort_by=sort_by, direction=direction, last_updated_at=last_updated_at, state=state
                )
                basic_prs.extend(additional_prs)

        print(f"{len(basic_prs)} 件のPull Requestの基本情報を取得しました")

        if not basic_prs:
            print("取得するPull Requestがありませんでした")
            return []

        print(f"Pull Requestの詳細情報を取得しています...")
        prs_data = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for pr in basic_prs:
                future = executor.submit(
                    self.process_pr,
                    pr,
                    include_comments=include_comments,
                    include_review_comments=include_review_comments,
                    include_commits=include_commits,
                    include_files=include_files,
                    include_labels=include_labels,
                )
                futures.append(future)

            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="PRs"):
                result = future.result()
                if result:
                    prs_data.append(result)

        print(f"{len(prs_data)} 件のPull Requestの詳細情報を取得しました")

        output_file = os.path.join(output_dir, "prs_data.json")
        self.save_to_json(prs_data, output_file)

        if prs_data and incremental:
            latest_updated_at = max(
                datetime.datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
                for pr in basic_prs
                if "updated_at" in pr
            )
            self.save_last_run_info(self.output_dir, latest_updated_at)

        if fetch_mode == "priority" or fetch_mode == "sequential":
            now_str = datetime.datetime.now().isoformat()
            for pr in prs_data:
                pr_id = str(pr["basic_info"]["number"])
                status_data[pr_id] = now_str
            self.save_pr_status_data(self.output_dir, status_data)

        return prs_data


def fetch_prs(
    repo_owner: str,
    repo_name: str,
    limit: Optional[int] = None,
    state: str = "all",
    sort_by: str = "updated",
    direction: str = "desc",
    include_comments: bool = True,
    include_review_comments: bool = True,
    include_commits: bool = True,
    include_files: bool = True,
    include_labels: bool = True,
    max_workers: int = 4,
    output_dir: Optional[str] = None,
    incremental: bool = False,
    fetch_mode: str = "api",
    start_id: int = 1,
    max_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Pull Requestデータを取得する便利関数

    Args:
        repo_owner: リポジトリのオーナー名
        repo_name: リポジトリ名
        limit: 取得するPRの最大数
        state: PRの状態 ("open", "closed", "all")
        sort_by: ソート基準 ("created", "updated", "popularity", "long-running")
        direction: ソート方向 ("asc" or "desc")
        include_comments: コメントを含めるかどうか
        include_review_comments: レビューコメントを含めるかどうか
        include_commits: コミット情報を含めるかどうか
        include_files: 変更ファイル情報を含めるかどうか
        include_labels: ラベル情報を含めるかどうか
        max_workers: 並列処理の最大ワーカー数
        output_dir: 出力ディレクトリ
        incremental: 増分更新を行うかどうか
        fetch_mode: 取得モード ("api", "sequential", "priority")
        start_id: 取得開始ID（sequential モードの場合）
        max_id: 取得終了ID（sequential モードの場合）

    Returns:
        取得したPRデータのリスト
    """
    fetcher = PRFetcher(repo_owner, repo_name)
    return fetcher.fetch_prs(
        limit=limit,
        state=state,
        sort_by=sort_by,
        direction=direction,
        include_comments=include_comments,
        include_review_comments=include_review_comments,
        include_commits=include_commits,
        include_files=include_files,
        include_labels=include_labels,
        max_workers=max_workers,
        output_dir=output_dir,
        incremental=incremental,
        fetch_mode=fetch_mode,
        start_id=start_id,
        max_id=max_id,
    )
