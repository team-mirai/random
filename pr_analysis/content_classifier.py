#!/usr/bin/env python3

import json
import os
from pathlib import Path

import backoff
import requests


class ContentClassifier:
    """PRの内容を分析し、適切なカテゴリに分類するクラス"""

    def __init__(self, api_key=None, repo_root=None):
        """初期化

        Args:
            api_key: OpenRouter APIキー（Noneの場合は環境変数から取得）
            repo_root: リポジトリのルートディレクトリ（Noneの場合はカレントディレクトリの親）
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            print("警告: OpenRouter APIキーが設定されていません。コンテンツ分類機能は無効になります。")
            self.api_key = None

        self.repo_root = Path(repo_root) if repo_root else Path(__file__).parent.parent
        self.existing_files = self._get_existing_files()

    def _get_existing_files(self):
        """リポジトリ内の既存のマークダウンファイルを取得する"""
        existing_files = []
        for path in self.repo_root.glob("**/*.md"):
            if "pr_analysis" not in str(path.relative_to(self.repo_root)):
                existing_files.append(path)
        return existing_files

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        max_tries=3,
    )
    def classify_content(self, pr_data):
        """PRの内容を分析して分類する

        Args:
            pr_data: PR情報を含む辞書

        Returns:
            dict: 分類結果（カテゴリ名、信頼度、説明を含む）
        """
        content = self._extract_pr_content(pr_data)

        result = self._analyze_with_openrouter(content)

        return result

    def _extract_pr_content(self, pr_data):
        """PRから分析に必要なテキストを抽出する"""
        texts = []

        basic = pr_data.get("basic_info", {})
        if basic.get("title"):
            texts.append(f"タイトル: {basic['title']}")
        if basic.get("body"):
            texts.append(f"説明: {basic['body']}")

        commits = pr_data.get("commits", [])
        commit_msgs = []
        for commit in commits:
            if commit.get("commit", {}).get("message"):
                commit_msgs.append(commit["commit"]["message"])
        if commit_msgs:
            texts.append("コミットメッセージ:\n" + "\n".join(commit_msgs))

        comments = pr_data.get("comments", [])
        comment_texts = []
        for comment in comments:
            if comment.get("body"):
                comment_texts.append(comment["body"])
        if comment_texts:
            texts.append("コメント:\n" + "\n".join(comment_texts))

        return "\n\n".join(texts)

    def _analyze_with_openrouter(self, text):
        """OpenRouter APIを使用してテキストを分析し、最も適切なカテゴリを判定する"""
        categories = [
            "教育",
            "経済財政",
            "科学技術",
            "デジタル民主主義",
            "医療",
            "子育て",
            "ビジョン",
            "産業政策",
            "行政改革",
            "その他政策",
            "エネルギー",
            "システム",
        ]

        url = "https://openrouter.ai/api/v1/chat/completions"

        prompt = f"""
あなたはPull Request (PR)の内容を分析し、最も適切なラベルカテゴリに分類する専門家です。
以下のPRの内容を分析し、最も適切なカテゴリを選択してください。

選択可能なカテゴリ:
{", ".join(categories)}

PRの内容:
{text}

以下の形式でJSON形式で回答してください。
{{
  "digest": "PRの3行説明(3文で)",
  "title": "内容を簡潔に表現したタイトル",
  "category": "最も適切なカテゴリの提案（上記のいずれかを選択）",
  "confidence": 0.0〜1.0の数値（確信度）,
  "explanation": "そのカテゴリの提案をした理由の説明"
}}

適切なカテゴリがない場合は "分類不能" としてください。
        """

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        data = {
            "model": "openai/gpt-4o",  # 高性能モデルを使用
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        try:
            content = result["choices"][0]["message"]["content"]
            classification = json.loads(content)
            return classification
        except (KeyError, json.JSONDecodeError) as e:
            print(f"APIレスポンスの解析に失敗しました: {e}")
            return {"category": "分類不能", "confidence": 0.0, "explanation": "APIレスポンスの解析に失敗しました"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PRの内容を分類するツール")
    parser.add_argument("--input", required=True, help="PRデータを含むJSONファイル")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        pr_data = json.load(f)

    classifier = ContentClassifier()
    result = classifier.classify_content(pr_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
